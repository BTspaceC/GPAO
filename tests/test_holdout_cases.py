import unittest
from collections import Counter
from pathlib import Path

from evals.workflow_case_schema import load_workflow_cases


ROOT = Path(__file__).parent.parent.resolve()


class TestHoldoutCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_workflow_cases(ROOT / "evals" / "holdout_cases.jsonl")

    def test_has_two_unseen_cases_per_workflow(self):
        self.assertEqual(len(self.cases), 12)
        counts = Counter(case.workflow for case in self.cases)
        self.assertEqual(set(counts.values()), {2})

    def test_holdout_requires_state_patch_not_legacy_full_state(self):
        for case in self.cases:
            self.assertIn("PRODUCES_VALID_STATE_PATCH_3_1", case.required_invariants)
            self.assertNotIn("PRODUCES_VALID_CASE_STATE_3", case.required_invariants)

    def test_holdout_ids_do_not_overlap_regression_ids(self):
        regression = load_workflow_cases(ROOT / "evals" / "workflow_cases.jsonl")
        self.assertTrue(
            {case.case_id for case in self.cases}.isdisjoint(
                {case.case_id for case in regression}
            )
        )


if __name__ == "__main__":
    unittest.main()
