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
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

def check_utf8_and_mojibake(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False, "Failed to decode as UTF-8."
    
    # 检测不可见 BOM 或几乎为空的情况
    if len(content.strip()) == 0:
        return False, "File is empty or contains only whitespace/BOM."
    
    # 检测常见乱码特征（如 GBK 强行 UTF-8 造成的替换字符或特定乱码字）
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

def check_markdown_links():
    link_pattern = re.compile(r'\[.*?\]\(([^)]+)\)')
    errors = []
    
    for md_file in ROOT.rglob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                for link in link_pattern.findall(line):
                    if link.startswith(('http://', 'https://', 'file://', 'mailto:')):
                        continue
                    clean_link = link.split('#')[0]
                    if not clean_link:
                        continue
                        
                    target_path = (md_file.parent / clean_link).resolve()
                    
                    # 检查是否越界
                    if not str(target_path).startswith(str(ROOT)):
                        errors.append(f"{md_file.relative_to(ROOT)}:{line_no} Link escapes repository root: {clean_link}")
                        continue
                        
                    if not target_path.exists():
                        errors.append(f"{md_file.relative_to(ROOT)}:{line_no} Broken link: {clean_link}")
                        
    return errors

def main():
    print("=== GPAO Repository Integrity Check ===")
    has_error = False
    
    # 1. 检查所有的 markdown 和 python 文件编码及内容
    for ext in ['*.md', '*.py']:
        for file_path in ROOT.rglob(ext):
            # Skip hidden dirs like .git
            if '.git' in str(file_path):
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
                    
    # 2. 检查 Markdown 断链
    link_errors = check_markdown_links()
    if link_errors:
        for err in link_errors:
            print(f"[FAIL] {err}")
        has_error = True

    # 3. 检查规则一致性 (禁止造数)
    # 简单扫描是否存在 "r = \d" 或者 "p < \d" 且没有 VERIFIED 标记的情况
    for case_file in ROOT.rglob('examples/**/*.md'):
        with open(case_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(r'r\s*=\s*0\.\d+', content) or re.search(r'p\s*<\s*0\.\d+', content):
                if 'VERIFIED' not in content:
                    print(f"[FAIL] {case_file.relative_to(ROOT)}: Contains statistical values without a VERIFIED status.")
                    has_error = True

    # 4. 检查硬编码百分比规则
    for adapter in ROOT.rglob('adapters/*.md'):
        with open(adapter, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(r'\(\d+%\)', content) and '默认权重' not in content:
                print(f"[FAIL] {adapter.relative_to(ROOT)}: Contains hardcoded percentage without rule override.")
                has_error = True

    if has_error:
        print("\n[FAIL] CI Check Failed. Please fix the above issues.")
        sys.exit(1)
    else:
        print("\n[OK] All CI Checks Passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
