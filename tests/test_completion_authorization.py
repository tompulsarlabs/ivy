"""Explicit additive capacity controls; these cases never run Docker or models."""
import copy
import tempfile
import unittest
from pathlib import Path

from ivy_acceptance.budget import BudgetBlocked, Limits
from ivy_acceptance.canonical import InvalidManifest, digest
from ivy_acceptance.storage import AttemptStore, read_record, write_record


class CompletionAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.now = 1000
        self.limits = Limits(32, 90, 3600)
        with self.store() as store:
            store.reserve("original-failure", "original-container", 10)
            store.finish("original-failure", "original-container", "execution_error", terminated=True)
            store.authorize_extension("Earlier explicit three-probe approval")
            for i, outcome in enumerate(("execution_error", "canceled", "timed_out")):
                store.reserve(str(i), "container-" + str(i), 10)
                store.finish(str(i), "container-" + str(i), outcome, terminated=True)
        self.now += 2000

    def store(self):
        return AttemptStore(self.path, {"purpose": "synthetic"}, self.limits, clock=lambda: self.now)

    def test_one_completion_preserves_all_history_and_survives_restart(self):
        prior = read_record(self.path / "ledger.json")
        with self.store() as store:
            grant = store.authorize_completion("Tom approved one completion probe")
            self.assertEqual(grant["prior_ledger_sha256"], digest(prior))
            for key in ("started_at", "limits", "binding", "attempts", "authorization_extension"):
                self.assertEqual(store.state[key], prior[key])
            store.reserve("completion", "completion-container", 90)
            store.finish("completion", "completion-container", "completed", terminated=True)
        before = (self.path / "ledger.json").read_bytes()
        with self.store() as store:
            self.assertEqual(len(store.state["attempts"]), 5)
            self.assertEqual(sum(row["seconds"] for row in store.state["attempts"]), 130)
            with self.assertRaises(BudgetBlocked):
                store.authorize_completion("renew")
            with self.assertRaises(BudgetBlocked):
                store.authorize_extension("renew old grant")
            with self.assertRaises(BudgetBlocked):
                store.reserve("sixth", "sixth-container", 1)
        self.assertEqual((self.path / "ledger.json").read_bytes(), before)

    def test_window_requires_full_reservation_and_no_clock_rollback(self):
        with self.store() as store:
            store.authorize_completion("approved")
        for now in (self.now - 1, self.now + 511):
            self.now = now
            before = (self.path / "ledger.json").read_bytes()
            with self.store() as store:
                with self.assertRaises(BudgetBlocked):
                    store.reserve("late", "late-container", 90)
            self.assertEqual((self.path / "ledger.json").read_bytes(), before)

    def test_original_aggregate_caps_still_apply(self):
        # Forty seconds are already consumed in this synthetic history.
        prior = read_record(self.path / "ledger.json")
        self.limits = Limits(32, 10, 40)
        prior["limits"] = {"max_attempts": 32, "per_attempt_seconds": 10, "total_seconds": 40}
        write_record(self.path / "ledger.json", prior)
        with self.store() as store:
            store.authorize_completion("approved")
            with self.assertRaises(BudgetBlocked):
                store.reserve("extra", "extra-container", 1)

    def test_blank_approval_and_unresolved_work_do_not_mutate_ledger(self):
        with self.store() as store:
            before = (self.path / "ledger.json").read_bytes()
            with self.assertRaises(BudgetBlocked):
                store.authorize_completion(" ")
            self.assertEqual((self.path / "ledger.json").read_bytes(), before)
            store.state["attempts"][-1]["termination_confirmed"] = False
            store._save()
            before = (self.path / "ledger.json").read_bytes()
            with self.assertRaises(BudgetBlocked):
                store.authorize_completion("approved")
            self.assertEqual((self.path / "ledger.json").read_bytes(), before)

    def test_malformed_or_widened_grant_rejected_after_restart(self):
        with self.store() as store:
            store.authorize_completion("approved")
        good = read_record(self.path / "ledger.json")
        for field, value in (("max_fresh_attempts", 2), ("window_seconds", 1200),
                             ("prior_attempt_count", 0), ("started_at", float("inf"))):
            with self.subTest(field=field):
                bad = copy.deepcopy(good)
                bad["completion_authorization"][field] = value
                if field == "started_at":
                    # canonical records reject non-finite JSON before storage.
                    with self.assertRaises((InvalidManifest, ValueError)):
                        write_record(self.path / "ledger.json", bad)
                else:
                    write_record(self.path / "ledger.json", bad)
                    with self.assertRaises(InvalidManifest):
                        with self.store():
                            pass
        write_record(self.path / "ledger.json", good)
