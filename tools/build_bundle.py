#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GPAO Bundle Builder
生成单文件可用的 GPAO.bundle.md
"""

import os
import sys
import json
from pathlib import Path
import hashlib

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / 'dist'

BUNDLE_ORDER = [
    'SKILL.md',
    'workflows/plan_assignment.md',
    'workflows/simulate_grading.md',
    'workflows/postmortem.md',
    'workflows/profile_teacher.md',
    'workflows/modify_assignment.md',
    'workflows/diagnose_assignment.md',
    'templates/assignment_intake.md',
    'templates/case_state.md',
    'templates/rubric_visibility_matrix.md',
    'templates/teacher_evidence_ledger.md',
    'templates/teacher_profile.md',
    'adapters/empirical_paper.md',
    'adapters/programming_project.md',
    'adapters/experiment_report.md',
    'adapters/general.md',
]

def render_bundle():
    """
    无副作用的纯函数，读取源文件并生成 Bundle 内容及 Manifest 字典。
    返回: (bundle_text, manifest_dict)
    """
    manifest_sources = {}
    source_set_hash_obj = hashlib.sha256()
    
    # 建立固定的源文件哈希集合来替代变动的 git commit
    for rel_path in BUNDLE_ORDER:
        file_path = ROOT / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"Error: Missing dependency {rel_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        source_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        manifest_sources[rel_path] = source_hash
        # 把路径和内容共同计算入总哈希，保证绝对一致性
        source_set_hash_obj.update(rel_path.encode('utf-8'))
        source_set_hash_obj.update(content.encode('utf-8'))

    source_set_sha256 = source_set_hash_obj.hexdigest()
    
    header = f"""<!--
======================================================================
GPAO (Grade Point Alignment Optimizer) Bundle
本文件由 tools/build_bundle.py 自动生成。请勿手工编辑！
如需修改，请修改源文件后重新构建。
Source Set SHA-256: {source_set_sha256}
======================================================================
-->

# GPAO Bundle (单文件分发版)

> **当前处于 Bundle Mode（全量上下文兼容分发）**。
> 当规则要求读取某个路径时，应在本文件中查找对应的 `<!-- SOURCE: path -->` 章节，不得请求外部文件。
> 本模式只通过 SOURCE 标记提供逻辑导航，不具备模块化安装模式的上下文级渐进加载。

"""
    content_chunks = [header]
    
    for rel_path in BUNDLE_ORDER:
        file_path = ROOT / rel_path
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content_chunks.append(f"<!-- SOURCE: {rel_path} -->\n\n")
        content_chunks.append(content)
        content_chunks.append("\n\n---\n\n")
        
    final_content = "".join(content_chunks)
    
    # Generate Bundle SHA-256
    bundle_sha256 = hashlib.sha256(final_content.encode('utf-8')).hexdigest()
    
    manifest_data = {
        "bundle": "GPAO.bundle.md",
        "bundle_sha256": bundle_sha256,
        "source_set_sha256": source_set_sha256,
        "sources": manifest_sources
    }
    
    return final_content, manifest_data

def write_bundle(output_dir):
    try:
        final_content, manifest_data = render_bundle()
    except Exception as e:
        print(e)
        return False
        
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    
    bundle_path = out_path / 'GPAO.bundle.md'
    manifest_path = out_path / 'bundle_manifest.json'
    
    with open(bundle_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
        
    print(f"Bundle built successfully at {bundle_path}")
    print(f"Source Set SHA-256: {manifest_data['source_set_sha256']}")
    print(f"Bundle SHA-256: {manifest_data['bundle_sha256']}")
    return True

if __name__ == "__main__":
    if not write_bundle(DIST_DIR):
        sys.exit(1)
    sys.exit(0)
