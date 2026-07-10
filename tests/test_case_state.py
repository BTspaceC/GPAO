import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "tools"))

from case_state import (
    apply_state_change,
    migrate_legacy_evidence,
    new_case_state,
    preference_transfer_state,
    transition_authorization,
    validate_case_state,
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


if __name__ == "__main__":
    unittest.main()
