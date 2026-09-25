"""Deterministic bridge controls; no Paperclip server, network, Docker or model."""
import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ivy_acceptance.canonical import digest
from ivy_acceptance.evidence_io import EvidenceError
from ivy_acceptance.paperclip_bridge import (AttemptStore, CONTRACT, EXPECTED, LocalPaperclip,
                                            assess_capture, publish_review)
from ivy_acceptance.paperclip_pilot import cleanup


def fixture():
    binding = {"company_id": "company", "issue_id": "issue", "executor_id": "worker",
               "reviewer_id": "reviewer", "run_id": "run", "contract_sha256": digest(CONTRACT)}
    record = {**binding, "run_status": "succeeded", "exit_code": 0, "stdout": json.dumps(EXPECTED)}
    return binding, {"record": record, "sha256": digest(record)}


def changed(envelope, **fields):
    record = {**envelope["record"], **fields}
    return {"record": record, "sha256": digest(record)}


class ReviewAPI:
    def __init__(self):
        self.actor = {"id": "reviewer", "companyId": "company"}
        self.issue = {"id": "issue", "companyId": "company", "status": "in_review",
                      "assigneeAgentId": "reviewer", "executionState": {
                          "currentStageType": "review", "currentParticipant": {"agentId": "reviewer"},
                          "returnAssignee": {"agentId": "worker"}}}
        self.runs = [{"id": "run", "contextSnapshot": {"issueId": "issue"}}]
        self.comments = []
        self.writes = 0
        self.lose_response = False

    def call(self, method, path, body=None):
        if path == "/api/agents/me":
            return self.actor
        if "heartbeat-runs?" in path:
            return self.runs
        if method == "GET":
            return self.comments if path.endswith("/comments") else self.issue
        self.writes += 1
        if method == "PATCH":
            self.issue["status"] = body["status"]
        self.comments.append({"authorAgentId": self.actor["id"], "body": body.get("comment", body.get("body"))})
        if self.lose_response:
            raise TimeoutError("simulated lost response after committed write")
        return self.issue


class PaperclipAssessmentTests(unittest.TestCase):
    def test_valid_fixture_does_not_award_model_or_semantic_pass(self):
        binding, envelope = fixture()
        result = assess_capture(binding, envelope)
        self.assertTrue(result["approve_review"])
        self.assertEqual(result["semantic_status"], "unverified")
        self.assertEqual(result["benchmark_status"], "evidence_incomplete")

    def test_empty_finding_and_fabricated_citation_are_not_accepted(self):
        binding, envelope = fixture()
        for output in ({"findings": []}, {"findings": [{"path": "missing", "line": 2, "explanation": "green"}]},
                       {"findings": [{"path": "transport.txt", "line": True, "explanation": "green"}]}):
            with self.subTest(output=output):
                result = assess_capture(binding, changed(envelope, stdout=json.dumps(output)))
                self.assertEqual(result["fixture_status"], "fail")
                self.assertFalse(result["approve_review"])

    def test_worker_pass_claim_cannot_replace_evidence(self):
        binding, envelope = fixture()
        result = assess_capture(binding, changed(envelope, stdout='{"verified":true,"status":"pass"}'))
        self.assertFalse(result["approve_review"])

    def test_cancel_timeout_failure_and_running_stay_unverified_even_with_good_output(self):
        binding, envelope = fixture()
        for state in ("cancelled", "timed_out", "failed", "running", "unknown"):
            with self.subTest(state=state):
                result = assess_capture(binding, changed(envelope, run_status=state))
                self.assertEqual(result["fixture_status"], "unverified")
                self.assertFalse(result["approve_review"])

    def test_success_requires_integer_zero_exit(self):
        binding, envelope = fixture()
        for exit_code in (None, False, "0", 1):
            self.assertFalse(assess_capture(binding, changed(envelope, exit_code=exit_code))["approve_review"])

    def test_malformed_duplicate_and_deep_output_fail(self):
        binding, envelope = fixture()
        for text in ("", '{"findings":[],"findings":[]}', "[" * 18 + "0" + "]" * 18):
            self.assertEqual(assess_capture(binding, changed(envelope, stdout=text))["fixture_status"], "fail")

    def test_ownership_run_and_contract_cannot_be_rebound_by_rehashing(self):
        binding, envelope = fixture()
        for field in ("company_id", "issue_id", "executor_id", "reviewer_id", "run_id", "contract_sha256"):
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                assess_capture(binding, changed(envelope, **{field: "other"}))

    def test_self_review_is_rejected(self):
        binding, envelope = fixture()
        binding["reviewer_id"] = "worker"
        with self.assertRaises(EvidenceError):
            assess_capture(binding, changed(envelope, reviewer_id="worker"))

    def test_changed_capture_checksum_rejected(self):
        binding, envelope = fixture()
        envelope["record"]["stdout"] = "changed"
        with self.assertRaises(EvidenceError):
            assess_capture(binding, envelope)


class PaperclipStoreTests(unittest.TestCase):
    def test_concurrent_delivery_and_restart_allow_one_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attempts.db"
            store = AttemptStore(path)
            binding, _ = fixture()
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: AttemptStore(path).reserve("delivery", binding), range(8)))
            self.assertEqual(results.count(True), 1)
            self.assertFalse(AttemptStore(path).reserve("delivery", binding))
            with self.assertRaises(EvidenceError):
                store.reserve("delivery", {**binding, "issue_id": "other"})

    def test_sealed_capture_rejects_tampering_even_with_recomputed_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.db")
            binding, envelope = fixture()
            store.reserve("delivery", binding)
            store.bind_run("delivery", "run")
            store.capture("delivery", envelope["record"])
            with self.assertRaises(EvidenceError):
                store.assess("delivery", changed(envelope, stdout='{"findings":[]}'))
            self.assertTrue(store.assess("delivery", envelope)["approve_review"])
            self.assertEqual(store.assess("delivery", envelope), store.assess("delivery", envelope))
            with self.assertRaises(EvidenceError):
                store.capture("delivery", envelope["record"])
            with self.assertRaises(EvidenceError):
                store.bind_run("delivery", "different-run")

    def test_unbound_dispatch_never_becomes_assessed_or_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.db")
            binding, envelope = fixture()
            store.reserve("delivery", binding)
            store.capture("delivery", envelope["record"])
            with self.assertRaises(EvidenceError):
                store.assess("delivery", envelope)
            self.assertFalse(store.reserve("delivery", binding))


class PaperclipReviewTests(unittest.TestCase):
    def test_cleanup_continues_after_one_failed_stop(self):
        calls = []
        class API:
            def call(self, method, path, body):
                calls.append((method, path))
                if len(calls) == 1:
                    raise TimeoutError()
        errors = cleanup(API(), ["worker", "reviewer"], [("worker", {"id": "key1"}), ("reviewer", {"id": "key2"})])
        self.assertEqual(errors, ["pause_failed"])
        self.assertEqual(len(calls), 4)
        self.assertEqual([method for method, _ in calls], ["POST", "POST", "DELETE", "DELETE"])

    def test_lost_response_reconciles_without_duplicate_write(self):
        binding, envelope = fixture()
        api = ReviewAPI()
        api.lose_response = True
        assessment = assess_capture(binding, envelope)
        with self.assertRaises(TimeoutError):
            publish_review(api, binding, assessment)
        self.assertEqual(publish_review(api, binding, assessment)["delivery"], "already_recorded")
        self.assertEqual(api.writes, 1)

    def test_worker_forged_comment_does_not_suppress_real_review(self):
        binding, envelope = fixture()
        assessment = assess_capture(binding, envelope)
        api = ReviewAPI()
        api.comments.append({"authorAgentId": "worker", "body": "ivy-assessment:" + digest(assessment)})
        self.assertEqual(publish_review(api, binding, assessment)["delivery"], "recorded")
        self.assertEqual(api.writes, 1)

    def test_failed_assessment_stays_in_review(self):
        binding, envelope = fixture()
        api = ReviewAPI()
        assessment = assess_capture(binding, changed(envelope, stdout='{"findings":[]}'))
        self.assertEqual(publish_review(api, binding, assessment)["issue_status"], "in_review")
        self.assertEqual(api.issue["status"], "in_review")

    def test_changed_actor_stage_or_company_refuses_write(self):
        binding, envelope = fixture()
        assessment = assess_capture(binding, envelope)
        for mutation in (lambda a: a.actor.update(id="worker"),
                         lambda a: a.issue.update(companyId="other"),
                         lambda a: a.issue.update(status="in_progress"),
                         lambda a: a.issue["executionState"].update(currentStageType="approval")):
            api = ReviewAPI()
            mutation(api)
            with self.assertRaises(EvidenceError):
                publish_review(api, binding, assessment)
            self.assertEqual(api.writes, 0)

    def test_assessment_for_another_run_cannot_be_published(self):
        binding, envelope = fixture()
        api = ReviewAPI()
        assessment = assess_capture(binding, envelope)
        assessment["run_id"] = "other"
        with self.assertRaises(EvidenceError):
            publish_review(api, binding, assessment)
        self.assertEqual(api.writes, 0)

    def test_newer_executor_attempt_invalidates_old_assessment(self):
        binding, envelope = fixture()
        api = ReviewAPI()
        api.runs.insert(0, {"id": "new-run", "contextSnapshot": {"issueId": "issue"}})
        with self.assertRaises(EvidenceError):
            publish_review(api, binding, assess_capture(binding, envelope))
        self.assertEqual(api.writes, 0)

    def test_only_explicit_localhost_endpoint_allowed(self):
        for url in ("https://example.com", "http://localhost:3197", "http://127.0.0.1",
                    "http://127.0.0.1:3197@evil.com", "http://127.0.0.1:3197/api"):
            with self.subTest(url=url), self.assertRaises(EvidenceError):
                LocalPaperclip(url)


if __name__ == "__main__":
    unittest.main()
