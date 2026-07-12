# -*- coding: utf-8 -*-
"""Offline scorer for GPAO semantic-entailment predictions.

The runner is provider-neutral: a model or human evaluator writes one JSONL
record per case using ``case_id`` and ``predicted_label``. This module validates
that file against the fixed corpus, then reports accuracy and dangerous false
negatives without calling any model API.
"""

import argparse
import json
from pathlib import Path

try:  # Support both ``python -m evals...`` and direct script execution.
    from .schemas import EntailmentLabel, is_dangerous_false_negative
except ImportError:  # pragma: no cover - exercised by direct CLI use
    from schemas import EntailmentLabel, is_dangerous_false_negative


EVAL_FILE = Path(__file__).parent / "semantic_entailment_cases.jsonl"
REQUIRED_CASE_FIELDS = frozenset(
    {"case_id", "group", "fact", "claim", "expected_label"}
)
REQUIRED_PREDICTION_FIELDS = frozenset({"case_id", "predicted_label"})


class EvaluationInputError(ValueError):
    """Raised when a corpus or predictions file cannot be scored safely."""


def _load_jsonl(path):
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationInputError(
                    f"Invalid JSON in {path} at line {line_number}: {exc.msg}"
                ) from exc
            if not isinstance(record, dict):
                raise EvaluationInputError(
                    f"Expected an object in {path} at line {line_number}."
                )
            records.append(record)
    return records


def _index_records(records, required_fields, label_field, source_name):
    valid_labels = {label.value for label in EntailmentLabel}
    indexed = {}
    for line_number, record in enumerate(records, start=1):
        missing = required_fields - record.keys()
        if missing:
            raise EvaluationInputError(
                f"Missing fields {sorted(missing)} in {source_name} record {line_number}."
            )

        case_id = record["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvaluationInputError(
                f"Invalid case_id in {source_name} record {line_number}."
            )
        if case_id in indexed:
            raise EvaluationInputError(f"Duplicate case_id {case_id!r} in {source_name}.")

        label = record[label_field]
        if label not in valid_labels:
            raise EvaluationInputError(
                f"Invalid {label_field} {label!r} for case {case_id!r}."
            )
        indexed[case_id] = record
    return indexed


def load_cases(path=EVAL_FILE):
    """Load and validate the reference corpus, preserving JSONL order."""
    records = _load_jsonl(path)
    _index_records(records, REQUIRED_CASE_FIELDS, "expected_label", "case corpus")
    return records


def load_predictions(path):
    """Load and validate provider-neutral prediction records."""
    records = _load_jsonl(path)
    _index_records(
        records,
        REQUIRED_PREDICTION_FIELDS,
        "predicted_label",
        "predictions",
    )
    return records


def evaluate_predictions(cases, predictions):
    """Score a complete prediction set against the supplied cases."""
    case_index = _index_records(
        cases, REQUIRED_CASE_FIELDS, "expected_label", "case corpus"
    )
    prediction_index = _index_records(
        predictions,
        REQUIRED_PREDICTION_FIELDS,
        "predicted_label",
        "predictions",
    )

    missing = sorted(set(case_index) - set(prediction_index))
    extra = sorted(set(prediction_index) - set(case_index))
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing predictions: {missing}")
        if extra:
            details.append(f"unknown case_ids: {extra}")
        raise EvaluationInputError("Prediction coverage mismatch; " + "; ".join(details))

    incorrect = []
    dangerous_false_negatives = []
    correct = 0
    for case in cases:
        case_id = case["case_id"]
        expected = case["expected_label"]
        predicted = prediction_index[case_id]["predicted_label"]
        if expected == predicted:
            correct += 1
            continue

        error = {
            "case_id": case_id,
            "expected_label": expected,
            "predicted_label": predicted,
        }
        incorrect.append(error)
        if is_dangerous_false_negative(expected, predicted):
            dangerous_false_negatives.append(error)

    total = len(cases)
    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "dangerous_false_negative_count": len(dangerous_false_negatives),
        "dangerous_false_negatives": dangerous_false_negatives,
        "incorrect_predictions": incorrect,
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Score provider-neutral semantic-entailment predictions JSONL."
    )
    parser.add_argument(
        "predictions",
        type=Path,
        help="JSONL file with case_id and predicted_label for every corpus case.",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=EVAL_FILE,
        help="Reference corpus JSONL (defaults to the bundled 16-case corpus).",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = evaluate_predictions(
            load_cases(args.cases), load_predictions(args.predictions)
        )
    except (EvaluationInputError, OSError) as exc:
        build_parser().error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
