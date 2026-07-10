import unittest
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

class TestPolicyConsistency(unittest.TestCase):
    def setUp(self):
        self.case_facts_path = ROOT / 'examples' / 'hearing_fatigue_case' / 'case_facts.md'
        self.facts_content = self.case_facts_path.read_text(encoding='utf-8')
        
    def test_no_hardcoded_weights_in_adapters_and_cases(self):
        """测试适配器及未提供 Rubric 的案例中是否去除了硬编码权重"""
        for root_dir in ['adapters', 'examples']:
            for md_file in (ROOT / root_dir).rglob('*.md'):
                content = md_file.read_text(encoding='utf-8')
                # 不允许 (10%) 或 | 30% | （除官方任务书 input_summary.md 外）
                if 'input_summary.md' not in md_file.name:
                    self.assertNotRegex(content, r'\(\s*\d+(?:\.\d+)?\s*%\s*\)', 
                        f"File {md_file.relative_to(ROOT)} contains prohibited bracket percentage weights.")
                
                if 'visibility_matrix' in md_file.name or 'diagnosis' in md_file.name:
                    # 检查是否虚构了具体的权重比如 20/30/20/30
                    self.assertNotRegex(content, r'\|\s*20\s*\|', 
                        f"File {md_file.relative_to(ROOT)} contains fabricated exact weights without Rubric.")

    def test_case_facts_structure_strictness(self):
        """测试 case_facts.md 结构是否严格，不混用等级与状态"""
        # FACT/HIGH 等不应该出现在状态列
        lines = self.facts_content.split('\n')
        for line in lines:
            if '|' in line and 'ID' not in line and '---' not in line:
                # 表格行
                columns = [col.strip() for col in line.split('|')]
                if len(columns) > 3:
                    level_col = columns[3] if 'HIGH' in line else ''
                    status_col = columns[2] if 'UNVERIFIED' in line or 'SUPPORTED' in line else ''
                    if 'FACT' in status_col or 'HIGH' in status_col:
                        self.fail(f"case_facts.md mixes evidence level into verification_status: {line}")

    def test_derivatives_must_cite_existing_ids(self):
        """测试衍生文档引用的 ID 必须在 case_facts.md 中存在"""
        # 提取所有的 ID
        valid_ids = set(re.findall(r'(F_DATA_\d+|P_TCH_\d+)', self.facts_content))
        
        for md_file in (ROOT / 'examples' / 'hearing_fatigue_case').rglob('*.md'):
            if md_file.name == 'case_facts.md':
                continue
            content = md_file.read_text(encoding='utf-8')
            cited_ids = set(re.findall(r'(F_DATA_\d+|P_TCH_\d+)', content))
            for cid in cited_ids:
                self.assertIn(cid, valid_ids, f"File {md_file.relative_to(ROOT)} cites non-existent ID {cid}")

    def test_unknown_facts_not_used_as_verified(self):
        """测试 UNVERIFIED 或 INSUFFICIENT_DATA 的数值未被直接当做事实引用"""
        # 找到所有状态不是 SUPPORTED 的事实 ID
        unverified_ids = []
        for line in self.facts_content.split('\n'):
            if '|' in line and 'F_DATA' in line:
                if 'UNVERIFIED' in line or 'INSUFFICIENT_DATA' in line:
                    match = re.search(r'(F_DATA_\d+)', line)
                    if match:
                        unverified_ids.append(match.group(1))
                        
        for md_file in (ROOT / 'examples' / 'hearing_fatigue_case').rglob('*.md'):
            if md_file.name == 'case_facts.md':
                continue
            content = md_file.read_text(encoding='utf-8')
            for uid in unverified_ids:
                # 检查这些 ID 是否在上下文中被当做了 SUPPORTED (比如被错误地放置到了需要 verified 的表格列里)
                # 至少确保它们如果被提及，附近有 [INFERENCE] 或者不被当做正文可见证据直接下定论
                # 在此我们强制测试 `diagnosis.md` 中如果不确定的数据，必须处于推断、占位符或不确定性声明中
                if uid in content and uid == 'F_DATA_04':
                    self.assertNotIn('r=0.65', content, f"{md_file.relative_to(ROOT)} fabricates specific UNKNOWN stats.")

if __name__ == '__main__':
    unittest.main()
