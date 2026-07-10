import unittest
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()


class TestWorkflowV3Contracts(unittest.TestCase):
    def _read(self, name):
        return (ROOT / "workflows" / name).read_text(encoding="utf-8")

    def test_all_workflows_use_case_state(self):
        for path in (ROOT / "workflows").glob("*.md"):
            self.assertIn("Case State", path.read_text(encoding="utf-8"), path.name)

    def test_diagnosis_avoids_certain_grade_claim(self):
        content = self._read("diagnose_assignment.md")
        self.assertNotIn("一定会在 30 秒内被老师打低分", content)
        self.assertIn("不得制造问题", content)

    def test_plan_has_defensive_mode(self):
        content = self._read("plan_assignment.md")
        self.assertIn("防御性规划模式", content)
        self.assertIn("不生成评分权重", content)

    def test_audit_marks_scan_as_heuristic(self):
        content = self._read("simulate_grading.md")
        self.assertIn("启发式", content)
        self.assertIn("不代表真实教师", content)

    def test_revision_authorization_state_machine(self):
        content = self._read("modify_assignment.md")
        for state in ("PREVIEW_ONLY", "APPLY_APPROVED", "APPLIED_AND_REAUDIT_REQUIRED"):
            self.assertIn(state, content)
        self.assertIn("未写入任何文件", content)

    def test_profile_uses_three_state_transfer(self):
        content = self._read("profile_teacher.md")
        self.assertIn("false/candidate/confirmed", content)
        self.assertIn("只有用户明确指定私有本地路径", content)

    def test_postmortem_forbids_score_reconstruction(self):
        self.assertIn("禁止从总分反推精确分项分数", self._read("postmortem.md"))

    def test_expression_linter_is_non_blocking(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "student_voice_auditor.py"), "--test"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("不用于AI文本鉴定", result.stdout)


if __name__ == "__main__":
    unittest.main()
