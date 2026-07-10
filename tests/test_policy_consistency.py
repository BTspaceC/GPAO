import unittest
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

ID_PATTERN = re.compile(r'\b(?:F_DATA|F_DOC|F_SCORE|F_FEEDBACK|F_SUBMISSION|P_TCH)_\d+[A-Z]?\b')

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
        """测试衍生文档引用的 ID 必须在 case_facts.md 中真实存在"""
        valid_ids = set()
        for line in self.facts_content.split('\n'):
            if '|' in line and '---' not in line and 'ID' not in line:
                cols = [col.strip() for col in line.split('|')]
                if len(cols) > 1 and cols[1]:
                    valid_ids.add(cols[1])
        
        for md_file in (ROOT / 'examples' / 'hearing_fatigue_case').rglob('*.md'):
            if md_file.name == 'case_facts.md':
                continue
            content = md_file.read_text(encoding='utf-8')
            cited_ids = set(ID_PATTERN.findall(content))
            for cid in cited_ids:
                self.assertIn(cid, valid_ids, f"File {md_file.relative_to(ROOT)} cites non-existent ID {cid}")

    def test_unknown_facts_not_used_as_verified(self):
        """测试非 SUPPORTED 的事实未被错误使用，禁止硬编码未验证数据"""
        for md_file in (ROOT / 'examples' / 'hearing_fatigue_case').rglob('*.md'):
            if md_file.name == 'case_facts.md':
                continue
            content = md_file.read_text(encoding='utf-8')
            
            self.assertNotIn('2小时导致疲劳', content, "Fabricated absolute threshold found!")
            self.assertNotIn('两小时阈值', content, "Fabricated absolute threshold found!")
            self.assertNotIn('r=0.65', content.replace(' ', ''), "Fabricated correlation value found!")
            self.assertNotIn('p<0.01', content.replace(' ', ''), "Fabricated p-value found!")

    def test_all_claims_must_have_id(self):
        """测试衍生文档的每一行有效陈述必须拥有合法身份（事实 ID 或对应的控制标记）"""
        for file_name in ['diagnosis.md', 'visibility_matrix.md', 'revised_strategy.md']:
            file_path = ROOT / 'examples' / 'hearing_fatigue_case' / file_name
            if not file_path.exists():
                continue
                
            lines = file_path.read_text(encoding='utf-8').split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # 过滤空行、标题、强调线
                if not line or line.startswith('#') or '---' in line:
                    continue
                # 过滤表格头部的格式
                if '|' in line and ('ID' in line or '评分项目' in line):
                    continue
                
                # 如果是表格内容行或普通文本行
                # 要求：有客观事实引用 ID，或者必须明确属于推断/建议/模板的特殊块
                has_id = bool(ID_PATTERN.search(line))
                is_inference = '[INFERENCE]' in line
                is_recommendation = '[RECOMMENDATION]' in line
                is_template = '[TEMPLATE]' in line
                
                # 特殊场景短句放行，保留目录性质词语和特殊结构标记
                is_structural = (
                    line in ['**现状问题**：', '**行动计划**：', '**收益**：'] or
                    line.startswith('**行动计划**') or 
                    line.startswith('**收益**') or 
                    line.startswith('**现状问题**') or 
                    line.startswith('本示例展示了如何使用') or 
                    line.startswith('最终得分与现有证据一致性分析') or 
                    line.startswith('经过复盘与诊断，我们制定以下具体修改策略') or
                    line.startswith('`schema_version') or
                    line.startswith('**声明：') or
                    line.startswith('*若现有问卷') or
                    line.startswith('*具体修改建议见') or
                    line.startswith('- **若')
                )
                
                if not (has_id or is_inference or is_recommendation or is_template or is_structural):
                    self.fail(f"Line {i+1} in {file_name} is an unclassified statement lacking ID or semantic tag:\n{line}")

    def test_percentage_matches_facts(self):
        """测试衍生文档中出现的权重不仅仅数值合法，且必须与 F_DOC 中的项目名称一一对应映射"""
        # 从 case_facts.md 动态提取 { 项目名称: 权重数值 } 映射
        doc_weights = {}
        for line in self.facts_content.split('\n'):
            if 'F_DOC' in line and '%' in line:
                cols = [c.strip() for c in line.split('|')]
                if len(cols) > 2:
                    claim = cols[2]
                    # 例如 "问卷设计与数据质量占比 25%。"
                    name_match = re.search(r'(.+?)占比', claim)
                    pct_match = re.search(r'(\d+(?:\.\d+)?)%', claim)
                    if name_match and pct_match:
                        doc_weights[name_match.group(1).strip()] = pct_match.group(1).strip()
                    
        self.assertTrue(len(doc_weights) > 0, "No valid weight mappings extracted from case_facts.md")
        
        for file_name in ['diagnosis.md', 'visibility_matrix.md']:
            file_path = ROOT / 'examples' / 'hearing_fatigue_case' / file_name
            if not file_path.exists():
                continue
                
            lines = file_path.read_text(encoding='utf-8').split('\n')
            for line in lines:
                if '|' in line and '%' in line:
                    cols = [c.strip() for c in line.split('|')]
                    # 假设表格前两列是 项目名称 和 权重
                    if len(cols) >= 3:
                        item_name = cols[1]
                        weight_str = cols[2].replace('%', '').strip()
                        
                        # 只要出现了带百分比的项，它的名称就必须在映射表中，防止造假新的评分项
                        self.assertIn(item_name, doc_weights, f"Fabricated scoring item found: '{item_name}' is not defined in case_facts.md")
                        
                        expected_weight = doc_weights[item_name]
                        self.assertEqual(weight_str, expected_weight, 
                            f"Weight mismatch in {file_name}: '{item_name}' should be {expected_weight}%, but found {weight_str}%")

if __name__ == '__main__':
    unittest.main()
