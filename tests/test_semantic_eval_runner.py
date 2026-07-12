# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
EVALS_DIR = ROOT / "evals"
RUNNER = EVALS_DIR / "run_semantic_entailment_eval.py"

sys.path.insert(0, str(ROOT))
from evals.run_semantic_entailment_eval import (  # noqa: E402
    EvaluationInputError,
    evaluate_predictions,
    load_cases,
    load_predictions,
)


def predictions_for(cases):
    return [
        {"case_id": case["case_id"], "predicted_label": case["expected_label"]}
        for case in cases
    ]


class TestSemanticEvalRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases()

    def test_perfect_predictions_report_full_accuracy(self):
        report = evaluate_predictions(self.cases, predictions_for(self.cases))
        self.assertEqual(report["total"], 16)
        self.assertEqual(report["correct"], 16)
        self.assertEqual(report["accuracy"], 1.0)
        self.assertEqual(report["dangerous_false_negative_count"], 0)
        self.assertEqual(report["dangerous_false_negatives"], [])

    def test_accepting_unsafe_claim_is_a_dangerous_false_negative(self):
        predictions = predictions_for(self.cases)
        target = next(item for item in predictions if item["case_id"] == "C_PREF_01")
        target["predicted_label"] = "ENTAILED"

        report = evaluate_predictions(self.cases, predictions)
        self.assertEqual(report["correct"], 15)
        self.assertEqual(report["accuracy"], 15 / 16)
        self.assertEqual(report["dangerous_false_negative_count"], 1)
        self.assertEqual(
            report["dangerous_false_negatives"][0],
            {
                "case_id": "C_PREF_01",
                "expected_label": "UNVERIFIED_AS_FACT",
                "predicted_label": "ENTAILED",
            },
        )

    def test_wrong_non_entailed_label_is_inaccurate_but_not_dangerous_fn(self):
        predictions = predictions_for(self.cases)
        target = next(item for item in predictions if item["case_id"] == "C_PREF_01")
        target["predicted_label"] = "OVERCLAIM"

        report = evaluate_predictions(self.cases, predictions)
        self.assertEqual(report["correct"], 15)
        self.assertEqual(report["dangerous_false_negative_count"], 0)

    def test_missing_unknown_duplicate_and_invalid_predictions_are_rejected(self):
        complete = predictions_for(self.cases)
        with self.assertRaisesRegex(EvaluationInputError, "missing predictions"):
            evaluate_predictions(self.cases, complete[:-1])

        with self.assertRaisesRegex(EvaluationInputError, "unknown case_ids"):
            evaluate_predictions(
                self.cases,
                complete + [{"case_id": "UNKNOWN", "predicted_label": "ENTAILED"}],
            )

        with self.assertRaisesRegex(EvaluationInputError, "Duplicate case_id"):
            evaluate_predictions(self.cases, complete + [dict(complete[0])])

        invalid = predictions_for(self.cases)
        invalid[0]["predicted_label"] = "MAYBE"
        with self.assertRaisesRegex(EvaluationInputError, "Invalid predicted_label"):
            evaluate_predictions(self.cases, invalid)

    def test_load_predictions_and_cli_emit_deterministic_json(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            prediction_path = Path(temporary_directory) / "predictions.jsonl"
            prediction_path.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False) + "\n"
                    for record in predictions_for(self.cases)
                ),
                encoding="utf-8",
            )
            self.assertEqual(len(load_predictions(prediction_path)), 16)

            completed = subprocess.run(
                [sys.executable, "-X", "utf8", str(RUNNER), str(prediction_path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["accuracy"], 1.0)
            self.assertEqual(report["dangerous_false_negative_count"], 0)


if __name__ == "__main__":
    unittest.main()
