import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from evals.behavior_eval import (  # noqa: E402
    BehaviorEvalError,
    build_provenance_manifest,
    build_report,
    export_blind_cases,
    load_run_files,
    load_runs,
    load_provenance,
    render_markdown,
)
from evals.workflow_case_schema import load_workflow_cases  # noqa: E402


class TestBehaviorEval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases_path = ROOT / "evals" / "workflow_cases.jsonl"
        cls.cases = load_workflow_cases(cls.cases_path)

    def _perfect_runs(self):
        runs = []
        for version in ("v2.1", "v3"):
            for repetition in (1, 2):
                for case in self.cases:
                    runs.append({
                        "run_id": f"{version}-{repetition}-{case.case_id}",
                        "version": version,
                        "repetition": repetition,
                        "case_id": case.case_id,
                        "failure_type": None,
                        "actual_route": case.expected_route,
                        "satisfied_invariants": list(case.required_invariants),
                        "observed_forbidden_behaviors": [],
                        "positive_action_taken": case.positive_action_required,
                        "citation_valid": True,
                        "contract_complete": True,
                        "input_tokens": 100,
                        "output_tokens": 100,
                        "duration_seconds": 1,
                        "retry_count": 0,
                    })
        return runs

    def _perfect_provenance(self, runs):
        digest = "a" * 64
        return [
            {
                "run_id": run["run_id"],
                "model": "test-model",
                "model_version": "test-version",
                "skill_version": "V2.1.0-RC1" if run["version"] == "v2.1" else "V3.0.0-RC1",
                "skill_sha256": ("b" if run["version"] == "v2.1" else "c") * 64,
                "input_files": ["SKILL.md", f"blind case {run['case_id']}"],
                "tool_policy": "read_only",
                "sampling_parameters": "not_configurable",
                "input_token_limit": 8000,
                "output_token_limit": 2000,
                "raw_output_ref": f"raw/{run['run_id']}.md",
                "raw_output_sha256": digest,
                "rubric_sha256": "d" * 64,
            }
            for run in runs
        ]

    def _report(self, runs):
        return build_report(self.cases, runs, self._perfect_provenance(runs))

    def test_blind_export_does_not_leak_expectations(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "blind.jsonl"
            self.assertEqual(export_blind_cases(self.cases_path, output), 24)
            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 24)
            for record in records:
                self.assertNotIn("expected_route", record)
                self.assertNotIn("required_invariants", record)
                self.assertNotIn("forbidden_behaviors", record)

    def test_perfect_matrix_passes_rc_gates(self):
        runs = self._perfect_runs()
        report = self._report(runs)
        self.assertEqual(report["protocol"]["expected_total_runs"], 96)
        self.assertTrue(report["rc1_passed"])
        self.assertTrue(all(report["rc1_gates"].values()))

    def test_serious_violation_and_over_refusal_fail(self):
        runs = self._perfect_runs()
        target = next(
            run for run in runs
            if run["version"] == "v3"
            and self.cases[[c.case_id for c in self.cases].index(run["case_id"])].positive_action_required
        )
        target["positive_action_taken"] = False
        target["observed_forbidden_behaviors"] = ["UNAUTHORIZED_WRITE"]
        report = self._report(runs)
        self.assertFalse(report["rc1_gates"]["observed_serious_violations_zero"])
        self.assertFalse(report["rc1_passed"])

    def test_run_loader_enforces_caps_and_failure_taxonomy(self):
        runs = self._perfect_runs()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runs.jsonl"
            runs[0]["failure_type"] = "NETWORK_MAYBE"
            path.write_text("\n".join(json.dumps(r) for r in runs), encoding="utf-8")
            with self.assertRaises(BehaviorEvalError):
                load_runs(path)

    def test_unexposed_token_and_duration_metadata_is_allowed(self):
        runs = self._perfect_runs()
        runs[0]["input_tokens"] = None
        runs[0]["output_tokens"] = None
        runs[0]["duration_seconds"] = None
        report = self._report(runs)
        self.assertEqual(report["versions"]["v2.1"]["metrics"]["payload_runs_unreported"], 1)

    def test_independent_judging_shards_can_be_loaded_together(self):
        runs = self._perfect_runs()
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.jsonl"
            second = Path(temp) / "second.jsonl"
            midpoint = len(runs) // 2
            first.write_text(
                "\n".join(json.dumps(r) for r in runs[:midpoint]), encoding="utf-8"
            )
            second.write_text(
                "\n".join(json.dumps(r) for r in runs[midpoint:]), encoding="utf-8"
            )
            loaded = load_run_files([first, second])
            self.assertEqual(len(loaded), len(runs))
            self.assertTrue(self._report(loaded)["rc1_passed"])

    def test_markdown_report_contains_protocol_failures_and_limitations(self):
        runs = self._perfect_runs()
        runs[0]["positive_action_taken"] = False
        report = self._report(runs)
        rendered = render_markdown(report)
        self.assertIn("协议摘要", rendered)
        self.assertIn(runs[0]["run_id"], rendered)
        self.assertIn("未覆盖风险", rendered)

    def test_missing_required_invariants_cannot_pass_rc(self):
        runs = self._perfect_runs()
        for run in runs:
            if run["version"] == "v3":
                run["satisfied_invariants"] = []
        report = self._report(runs)
        self.assertEqual(
            report["versions"]["v3"]["metrics"]["behavior_contract_pass_rate"],
            0.0,
        )
        self.assertFalse(report["rc1_passed"])

    def test_evaluator_or_model_failure_cannot_pass_rc(self):
        for failure_type in ("EVALUATOR_FAILURE", "MODEL_BEHAVIOR_FAILURE"):
            runs = self._perfect_runs()
            target = next(run for run in runs if run["version"] == "v3")
            target["failure_type"] = failure_type
            with self.subTest(failure_type=failure_type):
                self.assertFalse(self._report(runs)["rc1_passed"])

    def test_fabricated_data_is_a_critical_truthfulness_violation(self):
        runs = self._perfect_runs()
        target = next(run for run in runs if run["version"] == "v3")
        target["observed_forbidden_behaviors"] = ["FABRICATED_DATA"]
        report = self._report(runs)
        metrics = report["versions"]["v3"]["metrics"]
        self.assertEqual(metrics["serious_violation_count"], 1)
        self.assertEqual(metrics["safety_violation_counts"]["truthfulness"], 1)
        self.assertFalse(report["rc1_passed"])

    def test_privacy_safety_regression_is_compared_by_category(self):
        runs = self._perfect_runs()
        target = next(run for run in runs if run["version"] == "v3")
        target["observed_forbidden_behaviors"] = ["CROSS_COURSE_AUTO_CONFIRM"]
        report = self._report(runs)
        self.assertFalse(report["rc1_gates"]["safety_no_regression_vs_v2_1"])

    def test_unpinned_provenance_cannot_pass_rc(self):
        runs = self._perfect_runs()
        self.assertFalse(build_report(self.cases, runs)["rc1_passed"])

    def test_wrong_version_labels_and_string_booleans_are_rejected(self):
        runs = self._perfect_runs()
        runs[0]["version"] = "baseline"
        with self.assertRaises(BehaviorEvalError):
            build_report(self.cases, runs, self._perfect_provenance(runs))
        runs = self._perfect_runs()
        runs[0]["citation_valid"] = "false"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runs.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in runs), encoding="utf-8")
            with self.assertRaises(BehaviorEvalError):
                load_runs(path)

    def test_manifest_binds_every_run_to_raw_artifact_and_hashes(self):
        runs = self._perfect_runs()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "raw"
            raw.mkdir()
            for run in runs:
                (raw / f"{run['run_id']}.md").write_text(
                    "---\n"
                    f"run_id: {run['run_id']}\n"
                    "model: test-model\n"
                    "model_version: not_exposed\n"
                    "sampling_parameters: not_configurable\n"
                    "tool_policy: read_only\n"
                    "---\n\n# Response\n\nok\n",
                    encoding="utf-8",
                )
            rubric = root / "rubric.md"
            rubric.write_text("rubric", encoding="utf-8")
            output = root / "manifest.jsonl"
            count = build_provenance_manifest(
                runs,
                [raw],
                output,
                rubric,
                {"v2.1": "b" * 64, "v3": "c" * 64},
            )
            provenance = load_provenance(output)
            self.assertEqual(count, 96)
            self.assertEqual(len(provenance), 96)
            self.assertTrue(build_report(self.cases, runs, provenance)["rc1_passed"])


if __name__ == "__main__":
    unittest.main()
