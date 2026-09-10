"""Architecture acceptance checks using synthetic local inputs, never model calls."""
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ivy_acceptance.budget import BudgetBlocked, BudgetLedger, Limits
from ivy_acceptance.canonical import InvalidManifest, canonical_bytes, digest, read_json, snapshot_tree
from ivy_acceptance.planning import compile_plan, primary_slots, validate_schedule
from ivy_acceptance.ports import AttemptKind, CapabilityUnavailable, UnavailableAdapter, WorkerRequest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "examples/acceptance/preview.json"


class CanonicalTests(unittest.TestCase):
    def test_identity_is_canonical_but_arrays_and_content_are_significant(self):
        self.assertEqual(canonical_bytes({"b": 2, "a": "é"}), b'{"a":"\xc3\xa9","b":2}')
        self.assertEqual(digest({"b": 2, "a": 1}), digest({"a": 1, "b": 2}))
        self.assertNotEqual(digest([1, 2]), digest([2, 1]))
        self.assertNotEqual(digest({"a": 1}), digest({"a": 2}))

    def test_rejects_non_json_and_non_finite_values(self):
        for value in (math.nan, math.inf, {1: "x"}, (1, 2)):
            with self.subTest(value=value), self.assertRaises(InvalidManifest):
                canonical_bytes(value)

    def test_rejects_duplicate_keys_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            for value in ('{"schema_version":1,"schema_version":2}', '{"n":NaN}'):
                p.write_text(value)
                with self.assertRaises(InvalidManifest):
                    read_json(p)

    def test_snapshot_binds_content_and_executable_bit_and_rejects_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "task.md"
            p.write_text("Review the diff.")
            before = digest(snapshot_tree(root))
            p.chmod(0o755)
            self.assertNotEqual(before, digest(snapshot_tree(root)))
            p.write_text("Different assignment")
            self.assertNotEqual(before, digest(snapshot_tree(root)))
            (root / "outside").symlink_to("/etc/passwd")
            with self.assertRaises(InvalidManifest):
                snapshot_tree(root)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(CONFIG)

    def test_preview_is_detached_draft_and_instruction_only(self):
        envelope = compile_plan(self.config, ROOT)
        plan = envelope["plan"]
        self.assertEqual(envelope["plan_sha256"], digest(plan))
        self.assertNotIn("plan_sha256", plan)
        self.assertFalse(plan["execution_ready"])
        self.assertEqual(len(plan["primary_slots"]), 8)
        self.assertIn("R1:owner_review_pending", plan["blockers"])
        variants = plan["variants"]
        self.assertEqual(variants["baseline"]["agent_version"]["runtime"],
                         variants["changed"]["agent_version"]["runtime"])
        self.assertNotEqual(variants["baseline"]["agent_version_sha256"],
                            variants["changed"]["agent_version_sha256"])

    def test_compiled_plan_does_not_alias_mutable_input_or_other_variant(self):
        result = compile_plan(self.config, ROOT)
        original = copy.deepcopy(result)
        self.config["runtime"]["tools"].append("write-production")
        self.config["budget"]["max_attempts"] = 999
        self.assertEqual(result, original)
        result["plan"]["variants"]["changed"]["agent_version"]["runtime"]["tools"].append("new-tool")
        self.assertNotIn("new-tool", result["plan"]["variants"]["baseline"]["agent_version"]["runtime"]["tools"])
        self.assertNotEqual(result["plan_sha256"], digest(result["plan"]))

    def test_closed_schema_rejects_silent_runtime_drift_and_bad_paths(self):
        mutations = [
            lambda c: c.update(schema_version=2),
            lambda c: c.update(schema_version=True),
            lambda c: c.update(repetitions=True),
            lambda c: c["cases"].append(copy.deepcopy(c["cases"][0])),
            lambda c: c["cases"][0].update(worker_dir="../ivy"),
            lambda c: c["cases"][0].update(worker_dir="acceptance_fixtures//review/R1/worker"),
            lambda c: c["cases"][0].update(grader_dir=c["cases"][0]["worker_dir"]),
            lambda c: c["variants"]["changed"].update(requested_model="another-model"),
            lambda c: c["runtime"].update(environment_sha256="mutable-main"),
            lambda c: c["budget"].update(max_attempts=1),
            lambda c: c["budget"].update(total_seconds=90),
            lambda c: c["variants"]["changed"].update(instructions_dir="acceptance_fixtures/review/R1/grader"),
            lambda c: c["variants"]["changed"].update(instructions_dir="acceptance_fixtures/review"),
            lambda c: c["cases"][0].update(worker_dir="acceptance_fixtures/review"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                config = copy.deepcopy(self.config)
                mutate(config)
                with self.assertRaises(InvalidManifest):
                    compile_plan(config, ROOT)

    def test_six_cases_generate_exactly_24_paired_primary_slots(self):
        cases = [f"R{i}" for i in range(1, 7)]
        slots = primary_slots(cases, 2, 19)
        self.assertEqual(len(slots), 24)
        self.assertEqual(len({s["id"] for s in slots}), 24)
        self.assertEqual(slots, primary_slots(cases, 2, 19))
        for a, b in zip(slots[::2], slots[1::2]):
            self.assertEqual((a["case_id"], a["repetition"]), (b["case_id"], b["repetition"]))
            self.assertNotEqual(a["variant"], b["variant"])
        for malformed in (slots[:-1], slots + [slots[0]], list(reversed(slots))):
            with self.assertRaises(InvalidManifest):
                validate_schedule(malformed, cases, 2, 19)

    def test_planning_has_no_write_process_or_network_calls(self):
        # Imports happen before this scope; -B covers interpreter cache writes below.
        with patch("subprocess.Popen", side_effect=AssertionError("process call")), \
             patch("socket.socket", side_effect=AssertionError("network call")), \
             patch.object(Path, "write_text", side_effect=AssertionError("write")), \
             patch.object(Path, "write_bytes", side_effect=AssertionError("write")), \
             patch.object(Path, "mkdir", side_effect=AssertionError("mkdir")):
            self.assertFalse(compile_plan(self.config, ROOT)["plan"]["execution_ready"])

    def test_cli_preview_leaves_fresh_input_tree_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("ivy_acceptance", "acceptance_fixtures", "examples"):
                shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
            before = snapshot_tree(root)
            result = subprocess.run([sys.executable, "-B", "-m", "ivy_acceptance", "plan",
                                     "examples/acceptance/preview.json"], cwd=root,
                                    capture_output=True, text=True, check=True)
            self.assertFalse(json.loads(result.stdout)["plan"]["execution_ready"])
            self.assertEqual(before, snapshot_tree(root))


class BudgetTests(unittest.TestCase):
    def test_failed_attempts_are_consumed_and_duplicate_ids_cannot_retry(self):
        ledger = BudgetLedger(Limits(2, 90, 3600), 100)
        ledger.reserve("first", 100)
        ledger.finish("first", termination_confirmed=True)
        with self.assertRaises(BudgetBlocked):
            ledger.reserve("first", 101)
        ledger.reserve("diagnostic-second", 102)
        ledger.finish("diagnostic-second", termination_confirmed=True)
        with self.assertRaises(BudgetBlocked):
            ledger.reserve("third", 103)

    def test_unconfirmed_shutdown_retains_ownership_until_confirmation(self):
        ledger = BudgetLedger(Limits(3, 90, 3600), 100)
        ledger.reserve("first", 100)
        ledger.finish("first", termination_confirmed=False)
        with self.assertRaises(BudgetBlocked):
            ledger.reserve("second", 101)
        with self.assertRaises(BudgetBlocked):
            ledger.finish("not-the-owner", termination_confirmed=True)
        ledger.finish("first", termination_confirmed=True)
        ledger.reserve("second", 102)
        self.assertEqual(len(ledger.used), 2)

    def test_reserves_worst_case_time_and_rejects_invalid_clocks(self):
        ledger = BudgetLedger(Limits(3, 90, 100), 100)
        ledger.reserve("last-fit", 110)
        ledger.finish("last-fit", termination_confirmed=True)
        for now in (111, 109, math.nan, math.inf, True):
            with self.subTest(now=now), self.assertRaises(BudgetBlocked):
                ledger.reserve("next", now)


class AttemptIdentityTests(unittest.TestCase):
    def test_diagnostic_retry_cannot_masquerade_as_primary(self):
        request = dict(attempt_id="diagnostic-1", primary_slot_id="R1.1.baseline",
                       comparison_sha256="a" * 64, worker_snapshot_sha256="b" * 64,
                       agent_version_sha256="c" * 64, deadline_seconds=90)
        with self.assertRaises(ValueError):
            WorkerRequest(**request, diagnostic_of="primary-1")
        with self.assertRaises(ValueError):
            WorkerRequest(**request, kind=AttemptKind.DIAGNOSTIC)
        diagnostic = WorkerRequest(**request, kind=AttemptKind.DIAGNOSTIC, diagnostic_of="primary-1")
        self.assertEqual(diagnostic.kind, AttemptKind.DIAGNOSTIC)


class UnavailableAdapterTests(unittest.TestCase):
    def test_never_returns_simulated_execution_or_termination_success(self):
        adapter = UnavailableAdapter()
        self.assertFalse(adapter.describe()["available"])
        for invoke in (lambda: adapter.prepare(None), lambda: adapter.run(None, None),
                       lambda: adapter.cancel(None)):
            with self.assertRaises(CapabilityUnavailable):
                invoke()


if __name__ == "__main__":
    unittest.main()
