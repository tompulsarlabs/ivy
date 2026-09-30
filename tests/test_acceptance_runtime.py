"""Local safety and integrity controls; Docker is exercised explicitly, not mocked as proof."""
import copy
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from ivy_acceptance.budget import BudgetBlocked, Limits
from ivy_acceptance.canonical import InvalidManifest, digest, read_json
from ivy_acceptance.grading import check_citations
from ivy_acceptance.materialization import materialize_preview, pack_worker
from ivy_acceptance.planning import compile_plan
from ivy_acceptance.storage import AttemptStore, read_record, write_record


ROOT = Path(__file__).resolve().parents[1]


class DurableLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.now = 1000
        self.limits = Limits(3, 10, 30)

    def store(self, **kwargs):
        return AttemptStore(self.directory, {"comparison": "fixed"}, self.limits,
                            clock=lambda: self.now, **kwargs)

    def test_restart_keeps_unresolved_reservation_and_consumed_id(self):
        with self.store() as store:
            store.reserve("first", "container-first", 10)
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.reserve("second", "container-second", 10)
            store.finish("first", "container-first", "execution_error", terminated=False)
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.finish("first", "unowned", "execution_error", terminated=True)
            store.finish("first", "container-first", "execution_error", terminated=True)
            with self.assertRaises(BudgetBlocked):
                store.reserve("first", "container-first", 10)
            store.reserve("second", "container-second", 10)

    def test_os_lock_prevents_two_supervisors(self):
        with self.store():
            with self.assertRaises(BlockingIOError):
                with self.store():
                    self.fail("second supervisor acquired the lock")

    def test_ledger_rejects_corruption_changed_limits_and_invalid_rows(self):
        with self.store() as store:
            store.reserve("a", "container-a", 10)
        path = self.directory / "ledger.json"
        original = read_json(path)
        corrupt = copy.deepcopy(original)
        corrupt["record"]["attempts"] = []
        path.write_text(json.dumps(corrupt))
        with self.assertRaises(InvalidManifest):
            with self.store():
                pass
        write_record(path, original["record"])
        with self.assertRaises(InvalidManifest):
            with AttemptStore(self.directory, {"comparison": "fixed"}, Limits(4, 10, 40)):
                pass
        invalid = copy.deepcopy(original["record"])
        invalid["attempts"][0]["termination_confirmed"] = "true"
        write_record(path, invalid)
        with self.assertRaises(InvalidManifest):
            with self.store():
                pass

    def test_rollback_and_elapsed_budget_block_launch(self):
        with self.store():
            pass
        self.now = 999
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.reserve("a", "container-a", 10)
        self.now = 1021
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.reserve("a", "container-a", 10)

    def test_reserved_time_never_refunded(self):
        with self.store() as store:
            for i in range(3):
                store.reserve(str(i), "container-" + str(i), 10)
                store.finish(str(i), "container-" + str(i), "completed", terminated=True)
            with self.assertRaises(BudgetBlocked):
                store.reserve("four", "container-four", 1)

    def test_extension_preserves_history_and_cannot_renew_after_restart(self):
        with self.store() as store:
            store.reserve("old", "container-old", 3)
            store.finish("old", "container-old", "execution_error", terminated=True)
            original = copy.deepcopy(store.state)
        self.now += 100
        with self.store() as store:
            ext = store.authorize_extension("User approved 3 probes / 20 minutes")
            self.assertEqual(ext["prior_ledger_sha256"], digest(original))
            for key in ("started_at", "attempts", "limits", "binding"):
                self.assertEqual(store.state[key], original[key])
            store.reserve("fresh", "container-fresh", 10)
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.authorize_extension("renew")
            with self.assertRaises(BudgetBlocked):
                store.reserve("next", "container-next", 10)
            store.finish("fresh", "container-fresh", "completed", terminated=True)
            store.reserve("next", "container-next", 10)
            store.finish("next", "container-next", "completed", terminated=True)
            with self.assertRaises(BudgetBlocked):
                store.reserve("global-fourth", "container-fourth", 1)

    def test_extension_enforces_three_fresh_attempts_and_original_reserved_time(self):
        self.limits = Limits(32, 90, 3600)
        with self.store() as store:
            store.authorize_extension("approved")
            for number in range(3):
                name = str(number)
                store.reserve(name, "container-" + name, 90)
                store.finish(name, "container-" + name, "completed", terminated=True)
            with self.assertRaises(BudgetBlocked):
                store.reserve("four", "container-four", 1)
        # Separate synthetic ledger: extension cannot refund old reserved seconds.
        self.directory = self.directory / "reserved-cap"
        self.limits = Limits(32, 10, 10)
        with self.store() as store:
            store.reserve("old", "container-old", 10)
            store.finish("old", "container-old", "completed", terminated=True)
            store.authorize_extension("approved")
            with self.assertRaises(BudgetBlocked):
                store.reserve("fresh", "container-fresh", 1)

    def test_extension_window_includes_full_reservation_and_rejects_rollback(self):
        with self.store() as store:
            store.authorize_extension("approved")
        self.now += 1191
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.reserve("too-late", "container-late", 10)
        self.now = 999
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.reserve("rollback", "container-rollback", 1)

    def test_extension_requires_explicit_reference_and_known_shutdown(self):
        with self.store() as store:
            with self.assertRaises(BudgetBlocked):
                store.authorize_extension(" ")
            store.reserve("old", "container-old", 1)
            with self.assertRaises(BudgetBlocked):
                store.authorize_extension("approved")


class MaterializationTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(ROOT / "examples/acceptance/preview.json")
        self.envelope = compile_plan(self.config, ROOT)

    def test_only_worker_and_instruction_bytes_enter_archive(self):
        files, binding = materialize_preview(self.config, self.envelope, ROOT, "R1", "baseline")
        self.assertIn("fixture/task.md", files)
        self.assertIn("instructions/AGENTS.md", files)
        self.assertFalse(any("grader" in name or "labels" in name for name in files))
        with tarfile.open(fileobj=io.BytesIO(pack_worker(files))) as archive:
            names = {item.name for item in archive if item.isfile()}
            self.assertEqual(names, {"worker/" + name for name in files})
            for item in archive.getmembers():
                if item.isfile():
                    self.assertEqual(item.mode, 0o444)
        self.assertEqual(binding["plan_sha256"], self.envelope["plan_sha256"])

    def test_editing_execution_flag_even_with_new_digest_cannot_enable_preview(self):
        self.envelope["plan"]["execution_ready"] = True
        self.envelope["plan_sha256"] = digest(self.envelope["plan"])
        with self.assertRaises(InvalidManifest):
            materialize_preview(self.config, self.envelope, ROOT, "R1", "baseline")

    def test_changed_config_cannot_use_saved_plan(self):
        self.config["order_seed"] += 1
        with self.assertRaises(InvalidManifest):
            materialize_preview(self.config, self.envelope, ROOT, "R1", "baseline")


class GradingControls(unittest.TestCase):
    def test_fabricated_and_invalid_citations_fail_without_semantic_claims(self):
        files = {"fixture/head/code.py": b"first\nsecond\n"}
        for path, line in (("absent.py", 1), ("head/code.py", 3), ("head/code.py", True)):
            grade = check_citations({"findings": [{"path": path, "line": line, "explanation": "claim"}]}, files)
            self.assertEqual(grade["status"], "fail")
        grade = check_citations({"findings": [{"path": "head/code.py", "line": 2, "explanation": "claim"}]}, files)
        self.assertEqual(grade["status"], "pass")
        self.assertEqual(grade["semantic_status"], "unverified")
        self.assertEqual(grade["benchmark_status"], "evidence_incomplete")
