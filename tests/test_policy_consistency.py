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
                # 测试如果含有具体的 r/p/卡方，必须要求关联到 VERIFIED 或存在条件判断
                if re.search(r'r\s*=\s*0\.\d+', content) or re.search(r'p\s*[<=]\s*0\.\d+', content):
                    if 'VERIFIED' not in content and '实际输出' not in content:
                        self.fail(f"File {case_file.relative_to(ROOT)} contains statistical values without VERIFIED status or condition templates.")

    def test_no_hardcoded_weights_in_adapters(self):
        """测试适配器是否去除了默认权重"""
        for adapter_file in ROOT.rglob('adapters/*.md'):
            with open(adapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 使用正向拒绝机制，直接不允许带有括号的百分比或纯数字百分比作为权重出现
                # 这要求源文件表格里绝对干干净净。
                self.assertNotRegex(content, r'\(\s*\d+(?:\.\d+)?\s*%\s*\)', 
                    f"File {adapter_file.relative_to(ROOT)} contains prohibited bracket percentage weights.")
                
                # 还可以检查纯数字在表格线后紧跟着 % 的情况，如 `| xxx | 30% |`
                self.assertNotRegex(content, r'\|\s*\d+(?:\.\d+)?\s*%\s*\|',
                    f"File {adapter_file.relative_to(ROOT)} contains prohibited table percentage weights.")

    def test_evidence_levels_uniformity(self):
        """测试全仓使用统一的证据等级，无残留的“高/中/低”"""
        required_levels = ['FACT', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']
        skill_content = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        for level in required_levels:
            self.assertIn(level, skill_content, f"Evidence level {level} missing in SKILL.md")
            
        postmortem_content = (ROOT / 'workflows' / 'postmortem.md').read_text(encoding='utf-8')
        self.assertNotIn('高/中/低', postmortem_content, "Found outdated '高/中/低' in postmortem.md")

if __name__ == '__main__':
    unittest.main()
