import unittest
import json
import subprocess
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "tools"))

from case_state import (
    apply_state_patch,
    apply_state_change,
    migrate_legacy_evidence,
    new_case_state,
    new_state_patch,
    preference_transfer_state,
    transition_authorization,
    validate_case_state,
    validate_state_patch,
)


class TestCaseState(unittest.TestCase):
    def test_new_state_is_valid(self):
        self.assertEqual(validate_case_state(new_case_state("CASE_001")), [])

    def test_legacy_fact_is_not_upgraded(self):
        migrated = migrate_legacy_evidence({"claim": "老师喜欢复杂模型", "level": "FACT"})
        self.assertEqual(migrated["legacy_label"], "FACT")
        self.assertEqual(migrated["authority"], "unknown")
        self.assertEqual(migrated["verification"], "evidence_insufficient")
        self.assertEqual(migrated["confidence"], "unknown")
        self.assertEqual(migrated["transfer_state"], "false")

    def test_cross_field_change_requires_audit_record(self):
        state = new_case_state("CASE_002")
        with self.assertRaises(PermissionError):
            apply_state_change(state, "/审计", "constraints", ["只交 PDF"])
        apply_state_change(
            state,
            "/审计",
            "constraints",
            ["只交 PDF"],
            reason="审计时发现任务书要求",
            evidence_ids=["SRC_001"],
        )
        self.assertEqual(state["state_changes"][-1]["workflow"], "/审计")

    def test_sources_are_append_only(self):
        state = new_case_state("CASE_003")
        state["sources"] = [{"source_id": "SRC_001"}]
        with self.assertRaises(PermissionError):
            apply_state_change(
                state,
                "/诊断",
                "sources",
                [],
                reason="错误删除",
                evidence_ids=["SRC_001"],
            )

    def test_transfer_requires_distinct_courses_and_confirmation(self):
        evidence = [
            {"authority": "direct_feedback", "course": "A", "semantic_key": "chart_units", "verification": "supported"},
            {"authority": "direct_feedback", "course": "B", "semantic_key": "chart_units", "verification": "supported"},
        ]
        self.assertEqual(preference_transfer_state(evidence), "candidate")
        self.assertEqual(preference_transfer_state(evidence, explicitly_confirmed=True), "confirmed")

    def test_shared_template_does_not_transfer(self):
        evidence = [
            {"authority": "direct_feedback", "course": "A", "semantic_key": "three_line_table", "template_id": "COLLEGE_1"},
            {"authority": "direct_feedback", "course": "B", "semantic_key": "three_line_table", "template_id": "COLLEGE_1"},
        ]
        self.assertEqual(preference_transfer_state(evidence), "false")

    def test_authorization_state_machine(self):
        with self.assertRaises(PermissionError):
            transition_authorization("PREVIEW_ONLY", "APPLY_APPROVED")
        self.assertEqual(
            transition_authorization(
                "PREVIEW_ONLY", "APPLY_APPROVED", explicit_user_approval=True
            ),
            "APPLY_APPROVED",
        )
        self.assertEqual(
            transition_authorization(
                "APPLY_APPROVED",
                "APPLIED_AND_REAUDIT_REQUIRED",
                write_succeeded=True,
            ),
            "APPLIED_AND_REAUDIT_REQUIRED",
        )
        self.assertEqual(
            transition_authorization(
                "APPLIED_AND_REAUDIT_REQUIRED",
                "PREVIEW_ONLY",
                reaudit_completed=True,
            ),
            "PREVIEW_ONLY",
        )

    def test_new_state_patch_is_valid(self):
        patch = new_state_patch("CASE_004", "/诊断", base_state_available=False)
        patch["operations"] = [{
            "op": "set",
            "field": "stage",
            "value": "diagnosed",
            "reason": "完成初步诊断",
            "evidence_ids": ["SRC_001"],
        }]
        self.assertEqual(validate_state_patch(patch), [])

    def test_patch_without_base_cannot_invent_before_value(self):
        patch = new_state_patch("CASE_005", "/复盘", base_state_available=False)
        patch["operations"] = [{
            "op": "update_item",
            "field": "claims",
            "item_id": "CLM_001",
            "before": {"verification": "evidence_insufficient"},
            "updates": {"verification": "verified"},
            "reason": "收到教师反馈",
            "evidence_ids": ["SRC_002"],
        }]
        errors = validate_state_patch(patch)
        self.assertTrue(any("requires an available base state" in error for error in errors))

    def test_apply_patch_appends_and_records_change(self):
        state = new_case_state("CASE_006")
        patch = new_state_patch("CASE_006", "/诊断", base_state_available=False)
        patch["operations"] = [
            {
                "op": "append",
                "field": "sources",
                "value": {"source_id": "SRC_001"},
                "reason": "用户提供材料",
                "evidence_ids": ["SRC_001"],
            },
            {
                "op": "append",
                "field": "findings",
                "value": {"finding_id": "F_001", "text": "缺少任务书"},
                "reason": "输入未包含任务书",
                "evidence_ids": ["SRC_001"],
            },
        ]
        result = apply_state_patch(state, patch)
        self.assertEqual(result["findings"][0]["finding_id"], "F_001")
        self.assertEqual(result["state_changes"][-1]["field"], "findings")

    def test_update_item_checks_real_before_value(self):
        state = new_case_state("CASE_007")
        state["claims"] = [{
            "claim_id": "CLM_001",
            "authority": "direct_feedback",
            "verification": "evidence_insufficient",
            "confidence": "medium",
        }]
        state["sources"] = [{"source_id": "SRC_003"}]
        patch = new_state_patch("CASE_007", "/复盘", base_state_available=True)
        patch["operations"] = [{
            "op": "update_item",
            "field": "claims",
            "item_id": "CLM_001",
            "before": {"verification": "evidence_insufficient"},
            "updates": {"verification": "verified"},
            "reason": "教师反馈直接支持",
            "evidence_ids": ["SRC_003"],
        }]
        result = apply_state_patch(state, patch)
        self.assertEqual(result["claims"][0]["verification"], "verified")
        patch["operations"][0]["before"] = {"verification": "contradicted"}
        with self.assertRaises(ValueError):
            apply_state_patch(state, patch)

    def test_patch_rejects_untraceable_evidence_id(self):
        state = new_case_state("CASE_009")
        patch = new_state_patch("CASE_009", "/诊断", base_state_available=False)
        patch["operations"] = [{
            "op": "append",
            "field": "findings",
            "value": {"finding_id": "F_001"},
            "reason": "新增发现",
            "evidence_ids": ["MISSING"],
        }]
        with self.assertRaises(ValueError):
            apply_state_patch(state, patch)

    def test_patch_cli_validates_and_applies_json(self):
        state = new_case_state("CASE_010")
        patch = new_state_patch("CASE_010", "/诊断", base_state_available=False)
        patch["operations"] = [{
            "op": "append",
            "field": "sources",
            "value": {"source_id": "SRC_010"},
            "reason": "用户提供材料",
            "evidence_ids": ["SRC_010"],
        }]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path = root / "state.json"
            patch_path = root / "patch.json"
            output_path = root / "output.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            patch_path.write_text(json.dumps(patch), encoding="utf-8")
            validate = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "case_state.py"), "validate-patch", str(patch_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            apply = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "case_state.py"),
                    "apply-patch",
                    "--state", str(state_path),
                    "--patch", str(patch_path),
                    "--output", str(output_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(apply.returncode, 0, apply.stderr)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["sources"][0]["source_id"], "SRC_010")

    def test_no_base_patch_cannot_overwrite_an_existing_state(self):
        state = new_case_state("CASE_008")
        state["findings"] = [{"finding_id": "F_EXISTING"}]
        patch = new_state_patch("CASE_008", "/诊断", base_state_available=False)
        patch["operations"] = [{
            "op": "append",
            "field": "findings",
            "value": {"finding_id": "F_NEW"},
            "reason": "新增发现",
            "evidence_ids": ["SRC_001"],
        }]
        with self.assertRaises(ValueError):
            apply_state_patch(state, patch)


if __name__ == "__main__":
    unittest.main()
    new_state_patch,
