import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent.resolve()


class TestTriggerCases(unittest.TestCase):
    def setUp(self):
        path = ROOT / "evals" / "trigger_cases.jsonl"
        self.records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_records_are_well_formed_and_unique(self):
        self.assertGreaterEqual(len(self.records), 20)
        self.assertEqual(len({r["case_id"] for r in self.records}), len(self.records))
        for record in self.records:
            self.assertEqual(set(record), {"case_id", "category", "prompt", "expected_trigger"})
            self.assertIs(type(record["expected_trigger"]), bool)
            self.assertGreaterEqual(len(record["prompt"]), 15)

    def test_positive_and_negative_cases_are_balanced(self):
        positives = sum(r["expected_trigger"] for r in self.records)
        negatives = len(self.records) - positives
        self.assertGreaterEqual(positives, 8)
        self.assertGreaterEqual(negatives, 8)

    def test_required_categories_are_covered(self):
        categories = {r["category"] for r in self.records}
        for required in (
            "explicit_coursework_help",
            "implicit_rubric_alignment",
            "pre_submission_audit",
            "quick_audit",
            "postmortem",
            "english_alias",
            "ghostwriting_boundary",
            "ordinary_writing",
            "journal_submission",
            "general_coding",
        ):
            self.assertIn(required, categories)

    def test_ghostwriting_request_triggers_so_boundary_rules_apply(self):
        ghost = [r for r in self.records if r["category"] == "ghostwriting_boundary"]
        self.assertTrue(ghost)
        self.assertTrue(all(r["expected_trigger"] for r in ghost))


if __name__ == "__main__":
    unittest.main()
