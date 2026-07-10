# -*- coding: utf-8 -*-
import unittest
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
EVALS_DIR = ROOT / 'evals'

class TestEvalDatasetSchema(unittest.TestCase):
    def setUp(self):
        self.cases_file = EVALS_DIR / 'semantic_entailment_cases.jsonl'
        self.cases = []
        if self.cases_file.exists():
            with open(self.cases_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.cases.append(json.loads(line))

    def test_dataset_exists_and_size(self):
        self.assertTrue(self.cases_file.exists(), "semantic_entailment_cases.jsonl does not exist.")
        self.assertGreaterEqual(len(self.cases), 16, "Must have at least 16 evaluation cases.")

    def test_schema_correctness(self):
        # 导入 schemas 模块进行验证
        import sys
        sys.path.append(str(EVALS_DIR))
        from schemas import EntailmentLabel, EXPECTED_GROUPS
        
        case_ids = set()
        for case in self.cases:
            # 必填字段检查
            for field in ['case_id', 'group', 'fact', 'claim', 'expected_label']:
                self.assertIn(field, case, f"Missing {field} in case: {case.get('case_id', 'Unknown')}")
            
            # ID 唯一性
            case_id = case['case_id']
            self.assertNotIn(case_id, case_ids, f"Duplicate case_id: {case_id}")
            case_ids.add(case_id)
            
            # 标签合法性
            label = case['expected_label']
            valid_labels = [e.value for e in EntailmentLabel]
            self.assertIn(label, valid_labels, f"Invalid expected_label {label} in {case_id}")
            
            # 分组合法性
            self.assertIn(case['group'], EXPECTED_GROUPS, f"Invalid group {case['group']} in {case_id}")

if __name__ == '__main__':
    unittest.main()
