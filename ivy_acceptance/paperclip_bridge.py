"""Narrow, credential-free fixture assessment for the released Paperclip API.

This trusts the local operator and Paperclip's captured process output. It is
neither a worker sandbox nor an importer for Paperclip Runner native bundles.
"""
import json
import sqlite3
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import HTTPError

from .canonical import canonical_bytes, digest
from .evidence_io import EvidenceError, MAX_FILE, sha, strict_json
from .grading import check_citations

PAPERCLIP_VERSION = "2026.831.1"
FIXTURE = b"red\ngreen\nblue\n"
EXPECTED = {"findings": [{"path": "transport.txt", "line": 2, "explanation": "green"}]}
CONTRACT = {"schema": "ivy-paperclip-fixture/v1", "source_sha256": sha(FIXTURE),
            "expected_output_sha256": digest(EXPECTED)}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EvidenceError("paperclip_redirect_refused")


class LocalPaperclip:
    """Loopback-only API; tokens stay in memory and never enter evidence."""
    def __init__(self, url, token=None, run_id=None):
        parsed = urlsplit(url)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                or not parsed.port or parsed.username or parsed.password
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise EvidenceError("pilot_requires_explicit_ipv4_loopback_port")
        self.url, self.token = url.rstrip("/"), token
        self.run_id = run_id
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def call(self, method, path, body=None):
        if not path.startswith("/api/") or ".." in path or "#" in path:
            raise EvidenceError("invalid_api_path")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.run_id:
            headers["X-Paperclip-Run-Id"] = self.run_id
        request = Request(self.url + path, data=canonical_bytes(body) if body is not None else None,
                          headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=10) as response:
                data = response.read(MAX_FILE + 1)
        except HTTPError as exc:
            # Do not surface response bodies, request headers or tokens.
            raise EvidenceError(f"paperclip_http_{exc.code}") from None
        if len(data) > MAX_FILE:
            raise EvidenceError("paperclip_response_size_limit")
        return strict_json(data) if data else None


class AttemptStore:
    """Reserve before dispatch. Ambiguous attempts block redispatch, including after restart.

    This integration journal is separate from (and never opens) the historical
    Docker runtime store. It grants no Docker/model execution capacity.
    """
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS attempts (request_id TEXT PRIMARY KEY, "
                       "binding TEXT NOT NULL, run_id TEXT UNIQUE, capture TEXT, assessment TEXT)")

    def reserve(self, request_id, binding):
        encoded = canonical_bytes(binding).decode()
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT binding FROM attempts WHERE request_id=?", (request_id,)).fetchone()
            if row:
                if row[0] != encoded:
                    raise EvidenceError("duplicate_delivery_binding_mismatch")
                return False
            db.execute("INSERT INTO attempts(request_id,binding) VALUES (?,?)", (request_id, encoded))
        return True

    def bind_run(self, request_id, run_id):
        with sqlite3.connect(self.path) as db:
            if db.execute("UPDATE attempts SET run_id=? WHERE request_id=? AND run_id IS NULL",
                          (run_id, request_id)).rowcount != 1:
                raise EvidenceError("run_already_bound_or_not_reserved")

    def capture(self, request_id, capture):
        envelope = {"record": capture, "sha256": digest(capture)}
        with sqlite3.connect(self.path) as db:
            count = db.execute("UPDATE attempts SET capture=? WHERE request_id=? AND capture IS NULL",
                               (canonical_bytes(envelope).decode(), request_id)).rowcount
            if count != 1:
                raise EvidenceError("capture_missing_reservation_or_already_sealed")
        return envelope

    def assess(self, request_id, envelope):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT binding,capture,assessment,run_id FROM attempts WHERE request_id=?",
                             (request_id,)).fetchone()
            if not row or not row[1]:
                raise EvidenceError("attempt_capture_missing")
            if canonical_bytes(envelope).decode() != row[1]:
                raise EvidenceError("capture_differs_from_sealed_observation")
            if not row[3]:
                raise EvidenceError("attempt_run_unbound")
            result = assess_capture({**strict_json(row[0]), "run_id": row[3]}, envelope)
            encoded = canonical_bytes(result).decode()
            if row[2] and row[2] != encoded:
                raise EvidenceError("assessment_changed_on_replay")
            db.execute("UPDATE attempts SET assessment=? WHERE request_id=? AND assessment IS NULL",
                       (encoded, request_id))
        return result


def assess_capture(binding, envelope):
    """Assess the fixed transport fixture, never trust a reported verification flag."""
    if (type(envelope) is not dict or set(envelope) != {"record", "sha256"}
            or digest(envelope["record"]) != envelope["sha256"]):
        raise EvidenceError("capture_integrity_mismatch")
    record = envelope["record"]
    if (type(record) is not dict or set(record) != {
            "company_id", "issue_id", "executor_id", "reviewer_id", "run_id",
            "run_status", "exit_code", "stdout", "contract_sha256"}):
        raise EvidenceError("capture_schema_invalid")
    for field in ("company_id", "issue_id", "executor_id", "reviewer_id", "run_id"):
        if not isinstance(record[field], str) or not record[field] or record[field] != binding.get(field):
            raise EvidenceError("capture_ownership_mismatch")
    if record["executor_id"] == record["reviewer_id"]:
        raise EvidenceError("executor_cannot_review_itself")
    if record["contract_sha256"] != digest(CONTRACT) or binding.get("contract_sha256") != digest(CONTRACT):
        raise EvidenceError("fixture_contract_mismatch")
    result = {"schema": "ivy-paperclip-assessment/v1", "capture_sha256": envelope["sha256"],
              "issue_id": record["issue_id"], "run_id": record["run_id"],
              "fixture_status": "unverified", "citation_status": "unverified", "reasons": [],
              "semantic_status": "unverified", "benchmark_status": "evidence_incomplete",
              "evidence_kind": "deterministic_transport_fixture", "approve_review": False}
    if record["run_status"] not in {"succeeded", "failed", "timed_out", "cancelled"}:
        result["reasons"] = ["execution_not_terminal"]
        return result
    if record["run_status"] != "succeeded" or type(record["exit_code"]) is not int or record["exit_code"] != 0:
        result["reasons"] = ["execution_did_not_complete_successfully"]
        return result
    try:
        if type(record["stdout"]) is not str or len(record["stdout"].encode()) > MAX_FILE:
            raise EvidenceError("output_size_or_type_invalid")
        output = strict_json(record["stdout"])
        citations = check_citations(output, {"fixture/transport.txt": FIXTURE})
        result["citation_status"] = citations["status"]
        result["fixture_status"] = "pass" if output == EXPECTED and citations["status"] == "pass" else "fail"
        result["reasons"] = citations["failures"] or ([] if output == EXPECTED else ["fixed_fixture_output_mismatch"])
    except (EvidenceError, ValueError, TypeError):
        result["fixture_status"] = "fail"
        result["reasons"] = ["invalid_worker_output"]
    result["approve_review"] = result["fixture_status"] == "pass"
    return result


def publish_review(client, binding, assessment):
    """Reviewer-scoped write; recheck current ownership and reconcile a lost response.

    Failed/unverified assessments leave the task in review for operator action.
    A failed transport never triggers an automatic worker retry.
    """
    if (assessment.get("issue_id") != binding["issue_id"]
            or assessment.get("run_id") != binding["run_id"]
            or assessment.get("approve_review") != (assessment.get("fixture_status") == "pass")):
        raise EvidenceError("assessment_binding_mismatch")
    actor = client.call("GET", "/api/agents/me")
    if actor["id"] != binding["reviewer_id"] or actor["companyId"] != binding["company_id"]:
        raise EvidenceError("review_actor_mismatch")
    issue = client.call("GET", "/api/issues/" + binding["issue_id"])
    if issue["companyId"] != binding["company_id"] or binding["executor_id"] == actor["id"]:
        raise EvidenceError("review_ownership_mismatch")
    runs = client.call("GET", f"/api/companies/{binding['company_id']}/heartbeat-runs"
                       f"?agentId={binding['executor_id']}&limit=100")
    issue_runs = [run for run in runs if (run.get("contextSnapshot") or {}).get("issueId") == issue["id"]]
    # Paperclip returns newest first. A newer attempt invalidates an older review,
    # even when the same executor and reviewer still own the issue.
    if not issue_runs or issue_runs[0].get("id") != binding["run_id"]:
        raise EvidenceError("review_source_run_is_not_current")
    marker = "ivy-assessment:" + digest(assessment)
    comments = client.call("GET", "/api/issues/" + issue["id"] + "/comments")
    if any(c.get("authorAgentId") == actor["id"] and marker in c.get("body", "") for c in comments):
        return {"delivery": "already_recorded", "issue_status": issue["status"]}
    if issue["status"] != "in_review" or issue.get("assigneeAgentId") != actor["id"]:
        raise EvidenceError("review_stage_not_owned")
    state = issue.get("executionState") or {}
    principal = state.get("currentParticipant") or {}
    if principal.get("agentId") != actor["id"] or state.get("currentStageType") != "review":
        raise EvidenceError("review_policy_not_active")
    if (state.get("returnAssignee") or {}).get("agentId") != binding["executor_id"]:
        raise EvidenceError("review_executor_changed")
    body = marker + "\n" + json.dumps(assessment, sort_keys=True)
    if assessment["approve_review"]:
        response = client.call("PATCH", "/api/issues/" + issue["id"], {"status": "done", "comment": body})
        return {"delivery": "recorded", "issue_status": response["status"]}
    client.call("POST", "/api/issues/" + issue["id"] + "/comments", {"body": body})
    return {"delivery": "recorded", "issue_status": "in_review"}
