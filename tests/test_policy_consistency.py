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
                if 'input_summary.md' not in md_file.name:
                    self.assertNotRegex(content, r'\(\s*\d+(?:\.\d+)?\s*%\s*\)', 
                        f"File {md_file.relative_to(ROOT)} contains prohibited bracket percentage weights.")
                
                if 'visibility_matrix' in md_file.name or 'diagnosis' in md_file.name:
                    self.assertNotRegex(content, r'\|\s*20\s*\|', 
                        f"File {md_file.relative_to(ROOT)} contains fabricated exact weights without Rubric.")

    def test_case_facts_structure_strictness(self):
        """测试 case_facts.md 结构是否严格，不混用等级与状态，动态解析表头"""
        lines = self.facts_content.split('\n')
        
        current_status_idx = -1
        current_level_idx = -1
        
        for line in lines:
            if '|' in line and 'ID' in line and 'Claim' in line:
                headers = [h.strip() for h in line.split('|')]
                current_status_idx = next((i for i, h in enumerate(headers) if 'Verification' in h), -1)
                current_level_idx = next((i for i, h in enumerate(headers) if 'Level' in h), -1)
            elif '|' in line and 'ID' in line and 'Preference' in line:
                headers = [h.strip() for h in line.split('|')]
                current_status_idx = next((i for i, h in enumerate(headers) if 'Verification' in h), -1)
                current_level_idx = next((i for i, h in enumerate(headers) if 'Level' in h), -1)
            elif '|' in line and '---' not in line and 'ID' not in line:
                columns = [col.strip() for col in line.split('|')]
                if len(columns) > current_status_idx and current_status_idx != -1:
                    status_col = columns[current_status_idx]
                    if 'FACT' in status_col or 'HIGH' in status_col:
                        self.fail(f"case_facts.md mixes evidence level into verification_status: {line}")

    def test_derivatives_must_cite_existing_ids(self):
        """测试衍生文档引用的 ID 必须在 case_facts.md 中存在"""
        # 必须仅提取 case_facts.md 内真正注册定义的 ID，防止把衍生文档里造的 ID 当成有效的
        valid_ids = set()
        for line in self.facts_content.split('\n'):
            if '|' in line and '---' not in line and 'ID' not in line:
                # 假设 ID 始终在第一列
                cols = [col.strip() for col in line.split('|')]
                if len(cols) > 1 and cols[1]:
                    valid_ids.add(cols[1])
        
        for md_file in (ROOT / 'examples' / 'hearing_fatigue_case').rglob('*.md'):
            if md_file.name == 'case_facts.md':
                continue
            content = md_file.read_text(encoding='utf-8')
            cited_ids = set(re.findall(r'\b(?:F_DATA|F_DOC|F_SCORE|F_FEEDBACK|P_TCH)_\d+[A-Z]?\b', content))
            for cid in cited_ids:
                self.assertIn(cid, valid_ids, f"File {md_file.relative_to(ROOT)} cites non-existent ID {cid}")

    def test_unknown_facts_not_used_as_verified(self):
        """测试非 SUPPORTED 的事实未被错误使用，禁止硬编码未验证数据"""
        for md_file in (ROOT / 'examples' / 'hearing_fatigue_case').rglob('*.md'):
            if md_file.name == 'case_facts.md':
                continue
            content = md_file.read_text(encoding='utf-8')
            
            # 禁止凭空写明阈值
            self.assertNotIn('2小时导致疲劳', content, "Fabricated absolute threshold found!")
            self.assertNotIn('两小时阈值', content, "Fabricated absolute threshold found!")
            self.assertNotIn('r=0.65', content.replace(' ', ''), "Fabricated correlation value found!")
            self.assertNotIn('p<0.01', content.replace(' ', ''), "Fabricated p-value found!")

    def test_all_claims_must_have_id(self):
        """测试 diagnosis.md 和 visibility_matrix.md 中的分析陈述行，必须附带 ID 或 [INFERENCE]"""
        id_pattern = re.compile(r'\b(?:F_DATA|F_DOC|F_SCORE|F_FEEDBACK|P_TCH)_\d+[A-Z]?\b')
        
        for file_name in ['diagnosis.md', 'visibility_matrix.md']:
            file_path = ROOT / 'examples' / 'hearing_fatigue_case' / file_name
            if not file_path.exists():
                continue
                
            lines = file_path.read_text(encoding='utf-8').split('\n')
            for i, line in enumerate(lines):
                # 只检查表格中包含分析陈述的行
                if '|' in line and '---' not in line and 'ID' not in line and '评分项目' not in line:
                    has_id = bool(id_pattern.search(line))
                    has_inference = '[INFERENCE]' in line
                    
                    if not (has_id or has_inference):
                        self.fail(f"Line {i+1} in {file_name} lacks ID reference and [INFERENCE] tag:\n{line}")

if __name__ == '__main__':
    unittest.main()
