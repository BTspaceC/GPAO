#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GPAO 仓库完整性与发布验证器 (CI Checker)
运行该脚本以验证仓库是否符合发布门禁要求。
"""

import os
import re
import sys
import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
TEXT_GLOBS = ('*.md', '*.py', '*.json', '*.jsonl', '*.yml', '*.yaml')

def check_utf8_and_mojibake(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False, "Failed to decode as UTF-8."
    
    if content.startswith('\ufeff'):
        return False, "UTF-8 BOM detected. File must be UTF-8 without BOM."
        
    # 检测不可见 BOM 或几乎为空的情况
    if len(content.strip()) == 0:
        return False, "File is empty or contains only whitespace."
    
    # 检测常见乱码特征
    if '\ufffd' in content:
        return False, "Contains Unicode replacement character ''."
        
    if "ci_checker.py" not in file_path.name:
        mojibake_patterns = ['閫傞厤', '璇勫垎', '鏁版嵁', '涓庢牱', '鎬ф', '鏍稿績']
        for p in mojibake_patterns:
            if p in content:
                return False, f"Contains suspected mojibake pattern: '{p}'."
            
    return True, ""

def check_python_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Parse error: {e}"

def check_json_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix == '.jsonl':
                for line_no, line in enumerate(f, 1):
                    if line.strip():
                        json.loads(line)
            else:
                json.load(f)
        return True, ""
    except (json.JSONDecodeError, ValueError) as e:
        return False, f"Invalid JSON: {e}"

def check_tracked_private_files():
    """禁止把约定的私有材料或 raw 数据提交到仓库。"""
    result = subprocess.run(
        ['git', 'ls-files'],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=False,
    )
    if result.returncode != 0:
        return [f"Unable to inspect tracked files: {result.stderr.strip()}"]
    errors = []
    private_prefixes = (
        'private_assignments/', 'user_data/', 'profiles/private/',
        'evals/raw/', 'evals/raw_outputs/', 'evals/normalized/',
        'evals/private_reports/',
    )
    raw_suffixes = ('.raw.csv', '.raw.xlsx', '.raw.json')
    for raw_path in result.stdout.splitlines():
        normalized = raw_path.replace('\\', '/')
        if normalized.startswith(private_prefixes) or normalized.endswith(raw_suffixes):
            errors.append(f"Tracked private file: {raw_path}")
    return errors

def check_markdown_links():
    # 匹配常规的 Markdown 链接 [text](path) 以及代码块/内联代码中的 `path.md`
    md_link_pattern = re.compile(r'\[.*?\]\(([^)]+)\)')
    inline_link_pattern = re.compile(r'`([^`]+\.(?:md|py))`')
    errors = []
    
    for md_file in ROOT.rglob('*.md'):
        if '.git' in str(md_file) or 'dist' in str(md_file):
            continue
        # CHANGELOG 中可能会提到 python 脚本文件名，被工具误认为断链
        if md_file.name == 'CHANGELOG.md':
            continue
        with open(md_file, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                links_to_check = md_link_pattern.findall(line) + inline_link_pattern.findall(line)
                for link in links_to_check:
                    if link.startswith(('http://', 'https://', 'file://', 'mailto:')):
                        continue
                    clean_link = link.split('#')[0]
                    if not clean_link or clean_link.startswith('<'):
                        continue
                        
                    # 在反引号路由中，一般写为相对仓库根目录的路径，或者相对于当前文件的路径
                    # 如果不是 / 开头，先尝试相对于当前文件
                    target_path = (md_file.parent / clean_link).resolve()
                    
                    if not target_path.exists():
                        # 再尝试相对根目录
                        target_path = (ROOT / clean_link).resolve()
                        if not target_path.exists():
                            errors.append(f"{md_file.relative_to(ROOT)}:{line_no} Broken link: {clean_link}")
                            continue
                    
                    if not str(target_path).startswith(str(ROOT)):
                        errors.append(f"{md_file.relative_to(ROOT)}:{line_no} Link escapes repository root: {clean_link}")
                        
    return errors

def main():
    print("=== GPAO Repository Integrity Check ===")
    has_error = False
    
    for ext in TEXT_GLOBS:
        for file_path in ROOT.rglob(ext):
            if '.git' in str(file_path) or 'dist' in str(file_path):
                continue
                
            ok, msg = check_utf8_and_mojibake(file_path)
            if not ok:
                print(f"[FAIL] {file_path.relative_to(ROOT)}: {msg}")
                has_error = True
                
            if ext == '*.py':
                ok, msg = check_python_syntax(file_path)
                if not ok:
                    print(f"[FAIL] {file_path.relative_to(ROOT)}: {msg}")
                    has_error = True
            if ext in {'*.json', '*.jsonl'}:
                ok, msg = check_json_syntax(file_path)
                if not ok:
                    print(f"[FAIL] {file_path.relative_to(ROOT)}: {msg}")
                    has_error = True
                    
    link_errors = check_markdown_links()
    if link_errors:
        for err in link_errors:
            print(f"[FAIL] {err}")
        has_error = True

    privacy_errors = check_tracked_private_files()
    if privacy_errors:
        for err in privacy_errors:
            print(f"[FAIL] {err}")
        has_error = True

    if has_error:
        print("\n[FAIL] CI Check Failed. Please fix the above issues.")
        sys.exit(1)
    else:
        print("\n[OK] All CI Checks Passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
