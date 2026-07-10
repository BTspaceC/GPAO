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
from datetime import datetime
import hashlib
import subprocess

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / 'dist'
BUNDLE_PATH = DIST_DIR / 'GPAO.bundle.md'

BUNDLE_ORDER = [
    'SKILL.md',
    'workflows/plan_assignment.md',
    'workflows/simulate_grading.md',
    'workflows/postmortem.md',
    'templates/assignment_intake.md',
    'templates/rubric_visibility_matrix.md',
    'templates/teacher_evidence_ledger.md',
    'profiles/teacher_profile_template.md',
    'adapters/empirical_paper.md',
    'adapters/programming_project.md',
    'adapters/experiment_report.md',
]

def get_git_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT).decode('utf-8').strip()
    except Exception:
        return "unknown"

def build_bundle():
    DIST_DIR.mkdir(exist_ok=True)
    
    git_sha = get_git_commit()
    
    header = f"""<!--
======================================================================
GPAO (Grade Point Alignment Optimizer) Bundle
本文件由 tools/build_bundle.py 自动生成。请勿手工编辑！
如需修改，请修改源文件后重新构建。
Source Commit: {git_sha}
======================================================================
-->

# GPAO Bundle (单文件分发版)

"""
    content_chunks = [header]
    manifest_sources = {}
    
    for rel_path in BUNDLE_ORDER:
        file_path = ROOT / rel_path
        if not file_path.exists():
            print(f"Error: Missing dependency {rel_path}")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        source_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        manifest_sources[rel_path] = source_hash
            
        content_chunks.append(f"<!-- SOURCE: {rel_path} -->\\n\\n")
        content_chunks.append(content)
        content_chunks.append("\\n\\n---\\n\\n")
        
    final_content = "".join(content_chunks)
    
    with open(BUNDLE_PATH, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    # Generate SHA-256
    sha256 = hashlib.sha256(final_content.encode('utf-8')).hexdigest()
    
    manifest_data = {
        "bundle": "GPAO.bundle.md",
        "sha256": sha256,
        "commit": git_sha,
        "sources": manifest_sources
    }
    
    with open(DIST_DIR / 'bundle_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
        
    print(f"Bundle built successfully at {BUNDLE_PATH}")
    print(f"SHA-256: {sha256}")
    return True

if __name__ == "__main__":
    if not build_bundle():
        sys.exit(1)
    sys.exit(0)
