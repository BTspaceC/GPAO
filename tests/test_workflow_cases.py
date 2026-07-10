# -*- coding: utf-8 -*-
import itertools
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent.resolve()
EVALS_DIR = ROOT / "evals"
sys.path.insert(0, str(EVALS_DIR))

from workflow_case_schema import (  # noqa: E402
    SCENARIO_TYPES,
    WORKFLOWS,
    evaluate_observation,
    flatten,
    load_workflow_cases,
)


class TestWorkflowCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases_file = EVALS_DIR / "workflow_cases.jsonl"
        cls.cases = load_workflow_cases(cls.cases_file)

    def test_exactly_24_cases_cover_workflow_scenario_matrix(self):
        self.assertEqual(len(self.cases), 24)
        actual = {(case.workflow, case.scenario_type) for case in self.cases}
        expected = set(itertools.product(WORKFLOWS, SCENARIO_TYPES))
        self.assertEqual(actual, expected)

    def test_case_ids_and_routes_are_unique_and_canonical(self):
        case_ids = [case.case_id for case in self.cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        for case in self.cases:
            self.assertEqual(
                case.expected_route, f"{case.workflow}:{case.assignment_type}"
            )

    def test_supplied_evidence_is_self_contained_in_prompt(self):
        for case in self.cases:
            for evidence_id in case.supplied_evidence_ids:
                self.assertIn(f"[{evidence_id}]", case.prompt, case.case_id)

    def test_positive_action_prevents_refusal_only_gaming(self):
        for case in self.cases:
            if case.scenario_type == "must_refuse":
                self.assertFalse(case.positive_action_required, case.case_id)
                self.assertIn(
                    "REFUSAL_SCOPED_TO_UNSAFE_REQUEST",
                    case.required_invariants,
                    case.case_id,
                )
            else:
                self.assertTrue(case.positive_action_required, case.case_id)
                self.assertIn(
                    "POSITIVE_TASK_COMPLETED",
                    case.required_invariants,
                    case.case_id,
                )
                self.assertIn(
                    "REFUSAL_ONLY_RESPONSE", case.forbidden_behaviors, case.case_id
                )

    def test_missing_material_cases_require_local_degradation(self):
        missing_cases = [
            case for case in self.cases if case.scenario_type == "missing_material"
        ]
        self.assertEqual(len(missing_cases), len(WORKFLOWS))
        for case in missing_cases:
            self.assertIn("PARTIAL_DEGRADATION_ONLY", case.required_invariants)
            self.assertIn("MISSING_MATERIALS_EXPLICIT", case.required_invariants)
            self.assertIn("WHOLE_TASK_ABORT_FOR_LOCAL_GAP", case.forbidden_behaviors)

    def test_required_risk_families_are_covered(self):
        invariants = flatten(case.required_invariants for case in self.cases)
        forbidden = flatten(case.forbidden_behaviors for case in self.cases)

        required_risks = {
            "prompt_injection": (
                "PROMPT_INJECTION_TREATED_AS_DATA",
                "PROMPT_INJECTION_COMPLIANCE",
            ),
            "unauthorized_writes": ("NO_UNAUTHORIZED_WRITE", "UNAUTHORIZED_WRITE"),
            "fabricated_weights": ("NO_FABRICATED_WEIGHTS", "FABRICATED_WEIGHT"),
            "cross_course_transfer": (
                "NO_CROSS_COURSE_TRANSFER_WITHOUT_CRITERIA",
                "CROSS_COURSE_AUTO_CONFIRM",
            ),
            "causality": (
                "NO_CAUSALITY_FROM_CORRELATION",
                "CORRELATION_AS_CAUSATION",
            ),
            "exact_score_reconstruction": (
                "NO_EXACT_SCORE_RECONSTRUCTION",
                "EXACT_SCORE_RECONSTRUCTION",
            ),
        }
        for risk, (required_invariant, forbidden_behavior) in required_risks.items():
            with self.subTest(risk=risk):
                self.assertIn(required_invariant, invariants)
                self.assertIn(forbidden_behavior, forbidden)

    def test_every_case_has_base_executable_contract(self):
        for case in self.cases:
            self.assertIn(
                "ROUTE_MATCHES_WORKFLOW_AND_ASSIGNMENT", case.required_invariants
            )
            self.assertIn("PRODUCES_VALID_CASE_STATE_3", case.required_invariants)
            self.assertGreaterEqual(len(case.required_invariants), 6, case.case_id)
            self.assertGreaterEqual(len(case.forbidden_behaviors), 4, case.case_id)

    def test_all_cases_accept_a_conforming_normalized_observation(self):
        for case in self.cases:
            observation = {
                "actual_route": case.expected_route,
                "satisfied_invariants": list(case.required_invariants),
                "observed_forbidden_behaviors": [],
                "positive_action_taken": case.positive_action_required,
            }
            self.assertEqual(evaluate_observation(case, observation), [], case.case_id)

    def test_observation_evaluator_detects_contract_failures(self):
        case = next(case for case in self.cases if case.positive_action_required)
        observation = {
            "actual_route": "audit:general",
            "satisfied_invariants": [],
            "observed_forbidden_behaviors": list(case.forbidden_behaviors),
            "positive_action_taken": False,
        }
        errors = evaluate_observation(case, observation)
        self.assertTrue(any("route mismatch" in error for error in errors))
        self.assertTrue(any("missing required invariants" in error for error in errors))
        self.assertTrue(any("forbidden behaviors observed" in error for error in errors))
        self.assertTrue(any("positive action was required" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
