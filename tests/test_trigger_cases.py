import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent.resolve()


class TestTriggerCases(unittest.TestCase):
    def test_frozen_semantic_trigger_categories_are_covered(self):
        path = ROOT / "evals" / "trigger_cases.jsonl"
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(records), 5)
        self.assertEqual(
            {record["category"] for record in records},
            {
                "explicit_coursework_help",
                "implicit_rubric_alignment",
                "pre_submission_audit",
                "ordinary_writing",
                "casual_chat",
            },
        )
        self.assertEqual(sum(record["expected_trigger"] for record in records), 3)
        self.assertEqual(len({record["case_id"] for record in records}), 5)
        for record in records:
            self.assertIs(type(record["expected_trigger"]), bool)
            self.assertGreaterEqual(len(record["prompt"]), 15)


if __name__ == "__main__":
    unittest.main()
