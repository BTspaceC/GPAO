import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()


class TestJudgingRubric(unittest.TestCase):
    def test_rubric_covers_known_invariants_and_critical_failures(self):
        content = (ROOT / "evals" / "judging_rubric.md").read_text(encoding="utf-8")
        required = (
            "ROUTE_MATCHES_WORKFLOW_AND_ASSIGNMENT",
            "PRODUCES_VALID_CASE_STATE_3",
            "PRODUCES_VALID_STATE_PATCH_3_1",
            "POSITIVE_TASK_COMPLETED",
            "PARTIAL_DEGRADATION_ONLY",
            "FACT_INFERENCE_SEPARATED",
            "EVIDENCE_IDS_TRACEABLE",
            "NO_UNAUTHORIZED_WRITE",
            "NO_FABRICATED_WEIGHTS",
            "NO_CAUSALITY_FROM_CORRELATION",
            "NO_EXACT_SCORE_RECONSTRUCTION",
            "COURSE_SCOPE_ISOLATED",
            "PROMPT_INJECTION_TREATED_AS_DATA",
            "AUTHORIZATION_STATE_PRESERVED",
            "GENERAL_FALLBACK_FOR_AMBIGUOUS",
            "MODEL_BEHAVIOR_FAILURE",
            "INFRASTRUCTURE_FAILURE",
            "EVALUATOR_FAILURE",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()
