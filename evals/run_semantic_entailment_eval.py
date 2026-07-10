# -*- coding: utf-8 -*-
"""
执行大模型语义蕴含靶场测试。
仅在配置了有效 API Key 时手动运行。不进入 Required CI。
"""

import json
from pathlib import Path
from schemas import EntailmentLabel

EVAL_FILE = Path(__file__).parent / 'semantic_entailment_cases.jsonl'

def load_cases():
    cases = []
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            cases.append(json.loads(line))
    return cases

def mock_llm_predict(fact, claim):
    # 这里在实战阶段将接入真正的 LLM，目前作为桩函数抛出 Not Implemented
    raise NotImplementedError("LLM API not configured.")

def main():
    cases = load_cases()
    print(f"Loaded {len(cases)} evaluation cases.")
    
    # 评测指标
    total = len(cases)
    correct = 0
    overclaim_fn = 0  # 危险过度推断漏检数
    unverified_fn = 0 # 未验证事实接受数
    
    print("WARNING: This is a manual run script. LLM integration pending.")

if __name__ == "__main__":
    main()
