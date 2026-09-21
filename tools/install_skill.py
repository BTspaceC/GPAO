#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只安装 GPAO 运行时需要的文件（不含测试、评测数据和开发文档）。

用法：
    python tools/install_skill.py --target claude     # ~/.claude/skills/gpao
    python tools/install_skill.py --target codex      # $CODEX_HOME/skills/gpao 或 ~/.codex/skills/gpao
    python tools/install_skill.py --target D:/any/dir/gpao
    python tools/install_skill.py --target claude --dry-run
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

RUNTIME_FILES = (
    "SKILL.md",
    "LICENSE",
    "agents/openai.yaml",
    "tools/case_state.py",
    "tools/skim_view.py",
    "tools/student_voice_auditor.py",
)
RUNTIME_DIRS = ("workflows", "adapters", "templates")
MARKER = ".gpao-install"


def resolve_target(target: str) -> Path:
    if target == "claude":
        return Path.home() / ".claude" / "skills" / "gpao"
    if target == "codex":
        codex_home = os.environ.get("CODEX_HOME")
        base = Path(codex_home) if codex_home else Path.home() / ".codex"
        return base / "skills" / "gpao"
    return Path(target).expanduser()


def runtime_manifest() -> list[str]:
    files = list(RUNTIME_FILES)
    for directory in RUNTIME_DIRS:
        files += sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / directory).rglob("*.md")
        )
    return files


def install(destination: Path, *, dry_run: bool = False, force: bool = False) -> list[str]:
    files = runtime_manifest()
    if destination.resolve() == ROOT:
        raise ValueError("目标目录不能是仓库本身")
    if destination.exists() and any(destination.iterdir()):
        if not (destination / MARKER).exists() and not force:
            raise FileExistsError(
                f"{destination} 已存在且不是由本脚本安装的；确认可以覆盖时加 --force"
            )
    if dry_run:
        return files
    if destination.exists():
        shutil.rmtree(destination)
    for rel in files:
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    (destination / MARKER).write_text("installed by tools/install_skill.py\n", encoding="utf-8")
    return files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="安装 GPAO 运行时文件")
    parser.add_argument("--target", required=True, help="claude、codex 或任意目标目录")
    parser.add_argument("--dry-run", action="store_true", help="只列出将要复制的文件")
    parser.add_argument("--force", action="store_true", help="覆盖不是由本脚本创建的已有目录")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    destination = resolve_target(args.target)
    try:
        files = install(destination, dry_run=args.dry_run, force=args.force)
    except (FileExistsError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    verb = "将复制" if args.dry_run else "已安装"
    print(f"{verb} {len(files)} 个文件到 {destination}")
    for rel in files:
        print(f"  {rel}")
    if not args.dry_run:
        print("安装完成。重新打开 Claude Code 或 Codex 后即可使用 /诊断、/速审 等指令。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
