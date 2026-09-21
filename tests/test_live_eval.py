# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from evals import run_live_eval as live  # noqa: E402
from evals.behavior_eval import load_runs  # noqa: E402

CASES_PATH = ROOT / "evals" / "workflow_cases.jsonl"


def first_case():
    return live.read_jsonl(CASES_PATH)[0]


def completed(stdout, returncode=0, stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestPrompts(unittest.TestCase):
    def test_generation_prompt_is_blind(self):
        case = first_case()
        prompt = live.build_generation_prompt(case, "BUNDLE")
        self.assertIn(case["prompt"], prompt)
        self.assertNotIn(case["expected_route"], prompt)
        for invariant in case["required_invariants"]:
            self.assertNotIn(invariant, prompt)

    def test_installed_mode_prompt_invokes_skill(self):
        prompt = live.build_generation_prompt(first_case(), "")
        self.assertIn("$gpao", prompt)

    def test_bundle_context_matches_manifest(self):
        context, skill_hash = live.skill_context("bundle")
        self.assertIn("SOURCE: SKILL.md", context)
        self.assertEqual(len(skill_hash), 64)

    def test_command_resolution(self):
        self.assertEqual(live.resolve_command("claude", None), ["claude", "-p"])
        self.assertEqual(live.resolve_command("codex", None), ["codex", "exec", "-"])
        self.assertEqual(live.resolve_command("claude", "my-model --fast"), ["my-model", "--fast"])
        with self.assertRaises(live.LiveEvalError):
            live.resolve_command("unknown", None)


class TestCallModel(unittest.TestCase):
    @mock.patch("evals.run_live_eval.subprocess.run")
    def test_nonzero_exit_and_timeout_are_infrastructure_failures(self, run):
        run.return_value = completed("", returncode=1, stderr="boom")
        output, failure, _ = live.call_model(["x"], "p", 5)
        self.assertIsNone(output)
        self.assertIn("exit code 1", failure)
        run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=5)
        self.assertEqual(live.call_model(["x"], "p", 5)[1], "timeout")


class TestJudgeParsing(unittest.TestCase):
    def test_valid_judge_output_is_filtered_to_required_invariants(self):
        case = first_case()
        text = "结果如下：\n" + json.dumps({
            "actual_route": case["expected_route"],
            "satisfied_invariants": case["required_invariants"] + ["NO_UNAUTHORIZED_WRITE"],
            "observed_forbidden_behaviors": [],
            "positive_action_taken": True,
            "citation_valid": True,
            "contract_complete": True,
        })
        parsed = live.parse_judge_output(text, case)
        self.assertEqual(parsed["satisfied_invariants"], case["required_invariants"])

    def test_invalid_judge_output_is_rejected(self):
        case = first_case()
        with self.assertRaises(live.LiveEvalError):
            live.parse_judge_output("no json here", case)
        with self.assertRaises(live.LiveEvalError):
            live.parse_judge_output(json.dumps({"actual_route": "x"}), case)
        bad_label = json.dumps({
            "actual_route": "x", "satisfied_invariants": ["MADE_UP"],
            "observed_forbidden_behaviors": [], "positive_action_taken": True,
            "citation_valid": True, "contract_complete": True,
        })
        with self.assertRaises(live.LiveEvalError):
            live.parse_judge_output(bad_label, case)


class TestEndToEnd(unittest.TestCase):
    def test_generate_then_judge_produces_scorer_compatible_runs(self):
        case = first_case()
        judge_json = json.dumps({
            "actual_route": case["expected_route"],
            "satisfied_invariants": case["required_invariants"],
            "observed_forbidden_behaviors": [],
            "positive_action_taken": True,
            "citation_valid": True,
            "contract_complete": True,
        })
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            with mock.patch("evals.run_live_eval.subprocess.run", return_value=completed("模型回答")):
                self.assertEqual(live.main([
                    "generate", "--out", str(raw_dir), "--limit", "2", "--command", "fake",
                ]), 0)
            provenance = live.read_jsonl(raw_dir / "provenance.jsonl")
            self.assertEqual(len(provenance), 2)
            self.assertTrue(all(p["failure_type"] is None for p in provenance))
            self.assertTrue((raw_dir / provenance[0]["raw_output_ref"]).exists())

            runs_path = Path(tmp) / "runs.jsonl"
            with mock.patch("evals.run_live_eval.subprocess.run", return_value=completed(judge_json)):
                self.assertEqual(live.main([
                    "judge", "--raw-dir", str(raw_dir), "--out", str(runs_path), "--command", "fake",
                ]), 0)
            runs = load_runs(runs_path)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]["actual_route"], case["expected_route"])

    def test_infrastructure_failure_is_retried_once_and_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            with mock.patch(
                "evals.run_live_eval.subprocess.run",
                return_value=completed("", returncode=1, stderr="down"),
            ) as run:
                live.main(["generate", "--out", str(raw_dir), "--limit", "1", "--command", "fake"])
                self.assertEqual(run.call_count, 2)
            record = live.read_jsonl(raw_dir / "provenance.jsonl")[0]
            self.assertEqual(record["failure_type"], "INFRASTRUCTURE_FAILURE")
            self.assertEqual(record["retry_count"], 1)
            self.assertIsNone(record["raw_output_ref"])


class TestTriggers(unittest.TestCase):
    def test_description_is_read_from_frontmatter(self):
        self.assertIn("/速审", live.skill_description())

    def test_yes_no_parsing_and_scoring(self):
        self.assertTrue(live.parse_yes_no("YES"))
        self.assertFalse(live.parse_yes_no("答案：no"))
        self.assertIsNone(live.parse_yes_no("不确定"))
        report = live.score_triggers([
            {"case_id": "a", "expected": True, "predicted": True},
            {"case_id": "b", "expected": False, "predicted": True},
            {"case_id": "c", "expected": True, "predicted": None},
            {"case_id": "d", "expected": False, "predicted": False},
        ])
        self.assertEqual(report["accuracy"], 0.5)
        self.assertEqual(report["false_positives"], ["b"])
        self.assertEqual(report["false_negatives"], ["c"])
        self.assertEqual(report["unparsed"], 1)


if __name__ == "__main__":
    unittest.main()
