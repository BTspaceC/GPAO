# -*- coding: utf-8 -*-
import unittest
import json
from collections import Counter
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
        self.assertEqual(len(self.cases), 16, "The frozen corpus must contain exactly 16 cases.")

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

    def test_corpus_preserves_four_cases_per_group(self):
        import sys
        sys.path.append(str(EVALS_DIR))
        from schemas import EXPECTED_GROUPS

        counts = Counter(case['group'] for case in self.cases)
        self.assertEqual(counts, Counter({group: 4 for group in EXPECTED_GROUPS}))

    def test_known_semantic_regressions_are_labeled_conservatively(self):
        labels = {case['case_id']: case['expected_label'] for case in self.cases}
        self.assertEqual(labels['C_PREF_01'], 'UNVERIFIED_AS_FACT')
        self.assertEqual(labels['C_PREF_02'], 'OVERCLAIM')
        self.assertEqual(labels['C_WORK_02'], 'INSUFFICIENT_EVIDENCE')

if __name__ == '__main__':
    unittest.main()
