import unittest
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

class TestPolicyConsistency(unittest.TestCase):
    def test_no_fabricated_stats_in_examples(self):
        """测试示例中是否违反了禁止造数规则"""
        for case_file in ROOT.rglob('examples/**/*.md'):
            with open(case_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 匹配类似 r = 0.65 或 p < 0.05
                if re.search(r'r\s*=\s*0\.\d+', content) or re.search(r'p\s*[<=]\s*0\.\d+', content):
                    self.assertIn('VERIFIED', content, 
                        f"File {case_file.relative_to(ROOT)} contains statistical values without VERIFIED status.")

    def test_no_hardcoded_weights_in_adapters(self):
        """测试适配器是否去除了默认权重"""
        for adapter_file in ROOT.rglob('adapters/*.md'):
            with open(adapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 测试包含类似 (30%) 这样的硬编码分值
                if re.search(r'\(\d+%\)', content):
                    self.assertIn('默认权重', content, 
                        f"File {adapter_file.relative_to(ROOT)} contains percentage weights but no override rule.")
                    self.assertIn('禁止提供', content,
                        f"File {adapter_file.relative_to(ROOT)} must strictly prohibit default weights.")

    def test_evidence_levels_uniformity(self):
        """测试全仓使用统一的证据等级"""
        required_levels = ['FACT', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']
        skill_content = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        for level in required_levels:
            self.assertIn(level, skill_content, f"Evidence level {level} missing in SKILL.md")

if __name__ == '__main__':
    unittest.main()
