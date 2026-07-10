import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent.resolve()
ADAPTER_DIR = ROOT / "adapters"
ADAPTERS = (
    "empirical_paper.md",
    "programming_project.md",
    "experiment_report.md",
    "general.md",
)
REQUIRED_HEADINGS = (
    "## 识别信号",
    "## 反信号",
    "## 必要提问",
    "## 领域红线",
    "## 证据可见成果",
    "## 常见失败模式",
    "## 审计清单",
)


class TestAdapterContracts(unittest.TestCase):
    def read_adapter(self, name: str) -> str:
        return (ADAPTER_DIR / name).read_text(encoding="utf-8")

    def test_all_adapters_use_the_same_contract(self):
        for name in ADAPTERS:
            with self.subTest(adapter=name):
                content = self.read_adapter(name)
                positions = []
                for heading in REQUIRED_HEADINGS:
                    self.assertEqual(
                        content.count(heading),
                        1,
                        f"{name} must contain exactly one {heading!r} section",
                    )
                    positions.append(content.index(heading))
                self.assertEqual(
                    positions,
                    sorted(positions),
                    f"{name} contract sections are out of order",
                )

    def test_all_adapters_prohibit_fabricated_weights_and_facts(self):
        for name in ADAPTERS:
            with self.subTest(adapter=name):
                content = self.read_adapter(name)
                self.assertIn("默认权重：禁止提供", content)
                self.assertIn("不得编造评分权重", content)
                self.assertRegex(content, r"不得编造|不得编造、")

    def test_empirical_adapter_keeps_conditional_statistical_safeguards(self):
        content = self.read_adapter("empirical_paper.md")
        for safeguard in ("Likert", "有序变量", "信效度", "效应量", "置信区间", "因果", "风险阈值"):
            with self.subTest(safeguard=safeguard):
                self.assertIn(safeguard, content)
        self.assertNotIn("最好有稳健性检验", content)
        self.assertNotIn("必须降级为简单的相关或非参数检验", content)

    def test_general_adapter_is_an_uncertain_non_forcing_fallback(self):
        content = self.read_adapter("general.md")
        for invariant in ("类型不确定", "混合类型", "不强行", "不得因类型不明而强行套用", "缺失材料只降低相关部分"):
            with self.subTest(invariant=invariant):
                self.assertIn(invariant, content)


if __name__ == "__main__":
    unittest.main()
