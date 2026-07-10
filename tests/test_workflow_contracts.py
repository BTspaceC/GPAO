import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

class TestWorkflowContracts(unittest.TestCase):
    def test_all_workflows_load_adapters(self):
        """测试所有核心工作流是否都包含适配器加载指令"""
        workflows = ['plan_assignment.md', 'simulate_grading.md', 'postmortem.md']
        for wf in workflows:
            wf_path = ROOT / 'workflows' / wf
            content = wf_path.read_text(encoding='utf-8')
            self.assertIn('适配器', content, f"Workflow {wf} is missing adapter loading contract.")
            self.assertIn('类型', content, f"Workflow {wf} is missing assignment type identification.")
            self.assertIn('Case State', content, f"Workflow {wf} is missing shared state contract.")

    def test_deterministic_p0_p3_matrix(self):
        """测试规划工作流中是否包含硬性的 P0-P3 决策矩阵"""
        plan_content = (ROOT / 'workflows' / 'plan_assignment.md').read_text(encoding='utf-8')
        self.assertIn('**P0**', plan_content, "Missing deterministic P0 rule.")
        self.assertIn('硬性提交要求未满足', plan_content, "Missing hard-requirement P0 condition.")
        self.assertIn('人工覆盖优先级必须说明原因', plan_content, "Missing manual override requirement.")

    def test_postmortem_objectivity(self):
        """测试复盘准则是否已去主观化"""
        post_content = (ROOT / 'workflows' / 'postmortem.md').read_text(encoding='utf-8')
        self.assertIn('实际结果与现有证据是否一致', post_content, "Missing objective criteria in postmortem.")
        self.assertNotIn('得分是否合理', post_content, "Should not use subjective 'reasonable' check.")

if __name__ == '__main__':
    unittest.main()
