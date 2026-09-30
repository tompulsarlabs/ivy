"""Run the fixed, no-model Paperclip integration campaign on an isolated localhost instance.

Usage: python -m ivy_acceptance.paperclip_pilot --url http://127.0.0.1:3197 --state /new/path
The state directory is exclusive: reruns cannot replace evidence or silently retry.
"""
import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

from .canonical import canonical_bytes, digest
from .evidence_io import EvidenceError, sha
from .paperclip_bridge import (AttemptStore, CONTRACT, EXPECTED, PAPERCLIP_VERSION,
                              LocalPaperclip, publish_review)

def require(condition, reason):
    if not condition:
        raise EvidenceError(reason)


CASES = ("valid", "false_completion", "tampered", "duplicate_delivery", "interrupted")


def worker(case):
    # No credentials, files, shell commands or model calls are read or used.
    # The interrupted case emits no success artifact before cancellation.
    if case == "interrupted":
        time.sleep(30)
    output = EXPECTED if case != "false_completion" else {"findings": []}
    print(json.dumps(output), flush=True)


def write_new(path, value):
    data = canonical_bytes(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def wait_run(api, run_id, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = api.call("GET", "/api/heartbeat-runs/" + run_id)
        if run["status"] not in ("queued", "running"):
            return run
        time.sleep(0.15)
    raise EvidenceError("pilot_run_wait_deadline")


def heartbeat_config(enabled=False):
    return {"heartbeat": {"enabled": False, "intervalSec": 0, "wakeOnDemand": enabled}}


def cleanup(api, principal_ids, keys):
    """Attempt every stop and revocation even if one API operation fails."""
    errors = []
    actions = [("POST", f"/api/agents/{principal}/pause", {}) for principal in principal_ids]
    actions += [("DELETE", f"/api/agents/{principal}/keys/{key['id']}", None) for principal, key in keys]
    for method, path, body in actions:
        try:
            api.call(method, path, body)
        except Exception:
            errors.append("pause_failed" if method == "POST" else "key_revocation_failed")
    return errors


def run_case(api, root, company_id, case):
    case_dir = root / case
    case_dir.mkdir()
    store = AttemptStore(case_dir / "attempts.sqlite3")
    agent = api.call("POST", f"/api/companies/{company_id}/agents", {
        "name": "Fixture " + case, "role": "ceo", "adapterType": "process",
        "adapterConfig": {"command": sys.executable, "args": ["-B", "-m", "ivy_acceptance.paperclip_pilot", "--worker", case],
                          "cwd": str(Path(__file__).resolve().parents[1]), "timeoutSec": 10, "graceSec": 1},
        "runtimeConfig": heartbeat_config()})
    reviewer = api.call("POST", f"/api/companies/{company_id}/agents", {
        "name": "Ivy reviewer " + case, "role": "general", "reportsTo": agent["id"],
        "adapterType": "process", "adapterConfig": {"command": "/usr/bin/true", "timeoutSec": 5},
        "runtimeConfig": heartbeat_config()})
    issue = api.call("POST", f"/api/companies/{company_id}/issues", {
        "title": "Ivy deterministic transport: " + case,
        "description": "Return the fixed transport finding. Fixture-only integration, not semantic or model evaluation.",
        "status": "todo", "assigneeAgentId": agent["id"],
        "executionPolicy": {"mode": "normal", "commentRequired": True, "stages": [{
            "id": str(uuid.uuid4()), "type": "review", "approvalsNeeded": 1,
            "participants": [{"id": str(uuid.uuid4()), "type": "agent", "agentId": reviewer["id"]}]}]}})
    binding = {"company_id": company_id, "issue_id": issue["id"], "executor_id": agent["id"],
               "reviewer_id": reviewer["id"], "contract_sha256": digest(CONTRACT)}
    write_new(case_dir / "binding.json", binding)
    require(store.reserve(case, binding), "attempt_already_reserved")
    keys = []
    try:
        for principal in (agent, reviewer):
            key = api.call("POST", f"/api/agents/{principal['id']}/keys", {"name": "ivy-isolated-pilot"})
            keys.append((principal["id"], key))
        executor_api = LocalPaperclip(api.url, keys[0][1]["token"])
        reviewer_api = LocalPaperclip(api.url, keys[1][1]["token"])
        api.call("PATCH", "/api/agents/" + agent["id"], {"runtimeConfig": heartbeat_config(True)})
        run = api.call("POST", f"/api/agents/{agent['id']}/wakeup", {
            "source": "on_demand", "idempotencyKey": case,
            "payload": {"issueId": issue["id"]}})
        if not run.get("id"):
            raise EvidenceError("paperclip_did_not_dispatch")
        store.bind_run(case, run["id"])
        write_new(case_dir / "dispatched.json", {"run_id": run["id"]})
        api.call("PATCH", "/api/agents/" + agent["id"], {"runtimeConfig": heartbeat_config()})
        duplicate_refused = None
        completion_refused = None
        process_termination = "paperclip_report_only"
        if case == "duplicate_delivery":
            duplicate_refused = not AttemptStore(case_dir / "attempts.sqlite3").reserve(case, binding)
            require(duplicate_refused, "duplicate_dispatch_not_refused")
        if case == "interrupted":
            # Observe a running process before asking Paperclip to cancel it.
            for _ in range(40):
                observed = api.call("GET", "/api/heartbeat-runs/" + run["id"])
                if observed["status"] == "running" and type(observed.get("processPid")) is int and observed["processPid"] > 1:
                    break
                time.sleep(0.1)
            else:
                raise EvidenceError("interrupt_never_observed_running")
            api.call("POST", "/api/heartbeat-runs/" + run["id"] + "/cancel", {})
            # Paperclip may enqueue recovery independently of scheduled heartbeats.
            # Pause is part of this pilot's stop boundary, not an implicit retry grant.
            api.call("POST", "/api/agents/" + agent["id"] + "/pause", {})
            for _ in range(30):
                try:
                    os.kill(observed["processPid"], 0)
                except ProcessLookupError:
                    process_termination = "observed_worker_pid_absent_after_cancel"
                    break
                time.sleep(0.1)
            else:
                raise EvidenceError("worker_pid_still_present_after_cancel")
        terminal = wait_run(api, run["id"])
        executor_api.run_id = run["id"]
        if (terminal["companyId"] != company_id or terminal["agentId"] != agent["id"]
                or (terminal.get("contextSnapshot") or {}).get("issueId") != issue["id"]):
            raise EvidenceError("paperclip_run_ownership_mismatch")
        binding = {**binding, "run_id": run["id"]}
        result = terminal.get("resultJson") or {}
        capture = {**binding, "run_status": terminal["status"], "exit_code": terminal.get("exitCode"),
                   "stdout": result.get("stdout", "")}
        envelope = store.capture(case, capture)
        write_new(case_dir / "capture.json", envelope)
        tamper_rejected = None
        if case == "tampered":
            altered = json.loads(json.dumps(envelope))
            altered["record"]["stdout"] = '{"findings":[]}'
            # Even recomputing the checksum cannot replace the sealed observation.
            altered["sha256"] = digest(altered["record"])
            write_new(case_dir / "tampered-copy.json", altered)
            try:
                store.assess(case, altered)
            except EvidenceError:
                tamper_rejected = True
            else:
                raise EvidenceError("tampered_capture_accepted")
        assessment = store.assess(case, envelope)
        if case == "tampered":
            # Preserve the valid source result alongside the rejected delivery.
            write_new(case_dir / "original-assessment.json", assessment)
            assessment = {**assessment, "fixture_status": "fail", "citation_status": "unverified",
                          "approve_review": False, "reasons": ["capture_differs_from_sealed_observation"],
                          "rejected_delivery_sha256": altered["sha256"]}
        # Relay the executor's completion claim under its own local agent identity.
        # This is explicitly a supervisor-driven fixture, not an autonomous agent loop.
        try:
            executor_api.call("PATCH", "/api/issues/" + issue["id"], {
                "status": "done", "comment": "Fixture worker claims complete. Ivy must check captured evidence."})
        except EvidenceError as exc:
            if case != "interrupted" or str(exc) != "paperclip_http_409":
                raise
            completion_refused = True
        routed = api.call("GET", "/api/issues/" + issue["id"])
        if completion_refused:
            require(routed["status"] != "done" and not assessment["approve_review"], "cancelled_work_accepted")
            delivery = {"delivery": "cancelled_executor_completion_refused", "issue_status": routed["status"]}
        else:
            require(routed["status"] == "in_review" and routed["assigneeAgentId"] == reviewer["id"], "executor_bypassed_review")
            api.call("PATCH", "/api/agents/" + reviewer["id"], {"runtimeConfig": heartbeat_config(True)})
            review_run = api.call("POST", f"/api/agents/{reviewer['id']}/wakeup", {
                "source": "on_demand", "idempotencyKey": case + "-review",
                "payload": {"issueId": issue["id"]}})
            api.call("PATCH", "/api/agents/" + reviewer["id"], {"runtimeConfig": heartbeat_config()})
            if not review_run.get("id"):
                raise EvidenceError("paperclip_did_not_dispatch_reviewer")
            wait_run(api, review_run["id"])
            reviewer_api.run_id = review_run["id"]
            delivery = publish_review(reviewer_api, binding, assessment)
            replay = publish_review(reviewer_api, binding, assessment)
            require(replay["delivery"] == "already_recorded", "review_replay_not_reconciled")
        final_issue = api.call("GET", "/api/issues/" + issue["id"])
        runs = api.call("GET", f"/api/companies/{company_id}/heartbeat-runs?agentId={agent['id']}&limit=100")
        expected_done = case in ("valid", "duplicate_delivery")
        require((final_issue["status"] == "done") == expected_done, "unexpected_task_acceptance")
        processes = {r["processPid"] for r in runs if r.get("processPid")}
        require(len(processes) == 1, "unexpected_worker_process_count")
        require(all(r["status"] not in ("queued", "running") for r in runs), "outstanding_worker_run")
        if case != "interrupted":
            require(len(runs) == 1, "unexpected_run_record_count")
        summary = {"case": case, "control_passed": True, "issue_id": issue["id"], "run_id": run["id"],
                   "run_status": terminal["status"], "fixture_status": assessment["fixture_status"],
                   "final_issue_status": final_issue["status"], "paperclip_run_records": len(runs),
                   "worker_processes_observed": len(processes),
                   "automatic_retry_records": sum(bool(r.get("retryOfRunId")) for r in runs),
                   "duplicate_dispatch_refused": duplicate_refused, "tampered_copy_rejected": tamper_rejected,
                   "delivery": delivery, "capture_sha256": envelope["sha256"],
                   "model_quality": "unverified", "process_termination": process_termination,
                   "cancelled_completion_claim_refused": completion_refused}
        write_new(case_dir / "assessment.json", assessment)
        write_new(case_dir / "summary.json", summary)
        return summary
    finally:
        # Local Paperclip credentials only. Revoke even on a failed assertion.
        errors = cleanup(api, [agent["id"], reviewer["id"]], keys)
        if errors:
            write_new(case_dir / "cleanup-errors.json", {"errors": errors})
            if sys.exc_info()[0] is None:
                raise EvidenceError("pilot_cleanup_incomplete")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=CASES)
    parser.add_argument("--url")
    parser.add_argument("--state", type=Path)
    parser.add_argument("--case", choices=CASES, action="append")
    args = parser.parse_args(argv)
    if args.worker:
        worker(args.worker)
        return 0
    if not args.url or not args.state:
        parser.error("--url and --state are required")
    api = LocalPaperclip(args.url)
    health = api.call("GET", "/api/health")
    if health.get("version") != PAPERCLIP_VERSION or health.get("deploymentMode") != "local_trusted":
        raise EvidenceError("pilot_requires_pinned_local_paperclip")
    args.state.mkdir(parents=True, exist_ok=False)
    harness = {name: sha((Path(__file__).parent / name).read_bytes()) for name in
               ("paperclip_pilot.py", "paperclip_bridge.py", "grading.py", "canonical.py", "evidence_io.py")}
    write_new(args.state / "campaign.json", {"paperclip_version": PAPERCLIP_VERSION, "cases": args.case or list(CASES),
              "contract": CONTRACT, "provenance": "real_paperclip_process_adapter_fixed_fixture",
              "harness_sha256": harness, "python_version": sys.version, "optimization": sys.flags.optimize,
              "model_calls": 0, "historical_runtime_store_used": False})
    company = api.call("POST", "/api/companies", {"name": "Ivy isolated fixture pilot " + args.state.name})
    write_new(args.state / "company.json", {"id": company["id"]})
    summaries = []
    try:
        for case in args.case or CASES:
            summary = run_case(api, args.state, company["id"], case)
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
    except Exception as exc:
        write_new(args.state / "failure.json", {"error_type": type(exc).__name__,
                  "reason": str(exc) if isinstance(exc, EvidenceError) else "pilot_assertion_or_setup_failure",
                  "completed_cases": len(summaries)})
        raise
    write_new(args.state / "summary.json", {"controls": summaries, "all_controls_passed": True,
              "milestone_a": "not_passed", "model_calls": 0, "judge_calls": 0})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
