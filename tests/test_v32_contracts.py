# -*- coding: utf-8 -*-
"""V3.2 contracts: output layering, single routing table, AI policy, examples."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "tools"))

from case_state import FIELD_OWNERS, apply_state_patch, new_case_state, validate_state_patch  # noqa: E402

SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKFLOW_DIR = ROOT / "workflows"
TYPE_ROUTED_WORKFLOWS = (
    "diagnose_assignment.md",
    "plan_assignment.md",
    "simulate_grading.md",
    "quick_audit.md",
    "postmortem.md",
)
PATCH_HEADING = "状态补丁（供工具与后续工作流使用，可跳过）"
AI_JUDGEMENT = re.compile(r"AI\s*(痕迹|模板痕迹|生成概率|味)|像\s*AI\s*写")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class TestOutputLayering(unittest.TestCase):
    def test_skill_defines_layers_and_badges(self):
        self.assertIn("结论速览", SKILL)
        self.assertIn(PATCH_HEADING, SKILL)
        for badge in ("【已证实】", "【推断】", "【待确认】", "【已反驳】"):
            self.assertIn(badge, SKILL)

    def test_every_workflow_starts_with_summary(self):
        for path in WORKFLOW_DIR.glob("*.md"):
            with self.subTest(workflow=path.name):
                self.assertIn("结论速览", path.read_text(encoding="utf-8"))


class TestRouting(unittest.TestCase):
    def test_skill_has_single_routing_table_with_no_downgrade_rule(self):
        self.assertIn("作业类型路由（唯一权威来源）", SKILL)
        self.assertIn("已知类型不降级", SKILL)
        self.assertIn("次要成分不构成 mixed", SKILL)

    def test_type_routed_workflows_reference_table_and_forbid_downgrade(self):
        for name in TYPE_ROUTED_WORKFLOWS:
            content = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("第七节", content)
                self.assertIn("作业类型本身未知或确有跨类型组合", content)
                self.assertRegex(content, r"不得(将|把)?已知类型.{0,12}降级|已知类型不得.{0,20}降级")

    def test_specialised_adapters_no_longer_push_to_general(self):
        for name in ("empirical_paper.md", "programming_project.md", "experiment_report.md"):
            content = read(f"adapters/{name}")
            with self.subTest(adapter=name):
                self.assertIn("第七节", content)
                self.assertIn("不构成混合类型", content)
                self.assertNotIn("使用 `general` 或声明混合类型", content)

    def test_every_workflow_file_is_routed_from_skill(self):
        for path in WORKFLOW_DIR.glob("*.md"):
            with self.subTest(workflow=path.name):
                self.assertIn(f"workflows/{path.name}", SKILL)


class TestQuickAudit(unittest.TestCase):
    def test_quick_audit_is_registered_everywhere(self):
        self.assertIn("/速审", SKILL)
        self.assertIn("/quick", SKILL)
        self.assertIn("/速审", FIELD_OWNERS)
        self.assertIn("workflows/quick_audit.md", read("tools/build_bundle.py"))
        self.assertIn("`/速审`", read("templates/case_state.md"))

    def test_quick_audit_is_bounded(self):
        content = read("workflows/quick_audit.md")
        self.assertIn("不超过一屏", content)
        self.assertIn("最多 3 个", content)
        self.assertIn("不得为了凑满 3 条制造问题", content)


class TestAuthorizationConsistency(unittest.TestCase):
    def test_no_workflow_can_patch_authorization_state(self):
        for workflow, fields in FIELD_OWNERS.items():
            with self.subTest(workflow=workflow):
                self.assertNotIn("authorization_state", fields)

    def test_state_machine_is_identical_in_docs(self):
        back_edge = "--复审完成并记录结果--> PREVIEW_ONLY"
        self.assertIn(back_edge, read("workflows/modify_assignment.md"))
        self.assertIn(back_edge, read("templates/case_state.md"))
        self.assertNotIn("`authorization_state`、修改类", read("templates/case_state.md"))


class TestAiPolicy(unittest.TestCase):
    def test_policy_is_a_hard_constraint(self):
        self.assertIn("学术诚信与 AI 使用政策", SKILL)
        self.assertIn("代写边界", SKILL)
        self.assertIn("AI 使用政策未确认", SKILL)

    def test_policy_is_collected_and_checked(self):
        self.assertIn("AI 使用政策", read("templates/assignment_intake.md"))
        self.assertIn("CON_AI_POLICY", read("templates/case_state.md"))
        for name in ("plan_assignment.md", "simulate_grading.md", "quick_audit.md", "modify_assignment.md"):
            with self.subTest(workflow=name):
                self.assertIn("AI 使用政策", (WORKFLOW_DIR / name).read_text(encoding="utf-8"))


class TestConsistency(unittest.TestCase):
    def test_name_is_consistent(self):
        full_name = "Grading Preference Alignment Optimizer"
        for rel in ("SKILL.md", "README.md", "tools/build_bundle.py"):
            with self.subTest(file=rel):
                self.assertIn(full_name, read(rel))
                self.assertNotIn("Grade Point Alignment Optimizer", read(rel))

    def test_description_is_platform_neutral(self):
        frontmatter = SKILL.split("---")[1]
        self.assertNotIn("Codex", frontmatter)

    def test_no_reference_to_missing_profiles_directory(self):
        for path in list(ROOT.glob("*.md")) + list(ROOT.glob("*/*.md")):
            if path.name == "CHANGELOG.md" or "dist" in path.parts:
                continue
            for match in re.finditer(r"profiles/(\S*)", path.read_text(encoding="utf-8")):
                with self.subTest(file=path.name):
                    self.assertTrue(match.group(1).startswith("private/"), match.group(0))


class TestExampleOutputs(unittest.TestCase):
    EXAMPLES = sorted((ROOT / "test_runs").glob("*_example.md"))

    def test_every_workflow_family_has_an_example(self):
        self.assertGreaterEqual(len(self.EXAMPLES), 4)

    def _output_section(self, content):
        self.assertIn("## 示例输出", content)
        return content.split("## 示例输出", 1)[1]

    def test_examples_follow_layering(self):
        for path in self.EXAMPLES:
            output = self._output_section(path.read_text(encoding="utf-8"))
            with self.subTest(example=path.name):
                self.assertIn("### 结论速览", output)
                self.assertIn(PATCH_HEADING, output)
                self.assertLess(output.index("结论速览"), output.index(PATCH_HEADING))
                self.assertRegex(output, r"【(已证实|推断|待确认|已反驳)】")

    def test_examples_make_no_ai_authorship_judgement_or_invented_percentages(self):
        for path in self.EXAMPLES:
            output = self._output_section(path.read_text(encoding="utf-8"))
            with self.subTest(example=path.name):
                self.assertIsNone(AI_JUDGEMENT.search(output))
                self.assertIsNone(re.search(r"\d+(\.\d+)?\s*%", output))

    def test_example_patches_validate_and_apply(self):
        for path in self.EXAMPLES:
            output = self._output_section(path.read_text(encoding="utf-8"))
            blocks = re.findall(r"```json\n(.*?)\n```", output, re.S)
            with self.subTest(example=path.name):
                self.assertEqual(len(blocks), 1)
                patch = json.loads(blocks[0])
                self.assertEqual(validate_state_patch(patch), [])
                apply_state_patch(new_case_state(patch["case_id"]), patch)


if __name__ == "__main__":
    unittest.main()
