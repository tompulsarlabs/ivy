"""Deterministic fixture evidence only; these tests never execute an agent."""
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1] / "acceptance_fixtures"


def truth(case):
    return json.loads((ROOT / "review" / case / "grader" / "labels.json").read_text())


def function(case, revision, filename, name):
    return runpy.run_path(str(ROOT / "review" / case / "worker" / revision / filename))[name]


class FixtureExamples(unittest.TestCase):
    def test_r1_records_real_boundary_defect(self):
        fee = function("R1", "head", "shipping.py", "shipping_fee")
        mismatches = []
        for amount, expected in truth("R1")["ground_truth"]["behavior_checks"]:
            actual = fee(amount)
            if actual != expected:
                mismatches.append((amount, expected, actual))
        self.assertEqual(mismatches, [(5000, 0, 500)])

    def test_r3_preserves_tested_subtotals(self):
        before = function("R3", "base", "subtotal.py", "subtotal")
        after = function("R3", "head", "subtotal.py", "subtotal")
        for items, expected in truth("R3")["ground_truth"]["behavior_checks"]:
            with self.subTest(items=items):
                self.assertEqual(before(items), expected)
                self.assertEqual(after(items), expected)

    def test_drafts_have_no_claim_of_owner_approval(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for metadata in [manifest, truth("R1"), truth("R3")]:
            self.assertEqual(metadata["status"], "draft_requires_owner_review")
            self.assertIsNone(metadata["acceptance_owner"])


if __name__ == "__main__":
    unittest.main()
