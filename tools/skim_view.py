#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GPAO 30 秒视图生成器。

从作业文件中抽取老师快速浏览时最先看到的部分：标题、摘要/简介、各级标题、
图表标题、结论和附录引用，供 /审计 与 /速审 的可见性检查使用。

支持：.md/.markdown/.txt、.docx（仅标准库）、.pdf（需要可选依赖 pypdf）、
以及项目目录（读取 README 并汇总仓库结构）。

输出只是启发式抽取结果，不代表真实教师的阅卷方式，也不做任何 AI 文本判断。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

ABSTRACT_RE = re.compile(r"^(摘\s*要|内容摘要|简介|项目简介|概述|abstract|summary|overview)\b", re.I)
CONCLUSION_RE = re.compile(r"(结论|总结|结语|小结|conclusions?\b|summary and)", re.I)
APPENDIX_RE = re.compile(r"^(附\s*录|appendix|appendices)", re.I)
CAPTION_RE = re.compile(r"^\s*(图|表|figure|fig\.|table)\s*[0-9一二三四五六七八九十]+", re.I)
TXT_HEADING_RE = re.compile(
    r"^\s*(第[一二三四五六七八九十0-9]+[章节部分]|[一二三四五六七八九十]+、|[0-9]+(\.[0-9]+)*[\.、\s]\s*\S)"
)
RUN_HINT_RE = re.compile(r"(安装|运行|使用|部署|启动|install|usage|getting started|quick ?start|run)", re.I)
BODY_APPENDIX_REF_RE = re.compile(r"(附录\s*[A-Za-z0-9一二三四五六七八九十]?|appendix\s*[A-Z0-9]?)", re.I)

SOURCE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".kt", ".swift", ".m", ".r", ".R", ".scala",
}
IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".idea", ".vscode"}


@dataclass
class Block:
    kind: str  # "heading" | "para" | "caption"
    text: str
    level: int = 0


@dataclass
class SkimView:
    source: str
    kind: str
    title: str | None = None
    abstract: str | None = None
    outline: list[dict] = field(default_factory=list)
    captions: list[str] = field(default_factory=list)
    conclusion: str | None = None
    appendix_headings: list[str] = field(default_factory=list)
    appendix_refs_in_body: int = 0
    stats: dict = field(default_factory=dict)
    project: dict | None = None
    flags: list[str] = field(default_factory=list)


def _clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "……"


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def blocks_from_markdown(text: str) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    in_code = False

    def flush():
        if paragraph:
            joined = " ".join(paragraph).strip()
            if joined:
                blocks.append(Block("caption" if CAPTION_RE.match(joined) else "para", joined))
            paragraph.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", stripped)
        if heading:
            flush()
            blocks.append(Block("heading", heading.group(2), len(heading.group(1))))
            continue
        image = re.match(r"^!\[([^\]]*)\]\([^)]*\)", stripped)
        if image:
            flush()
            if image.group(1).strip():
                blocks.append(Block("caption", image.group(1).strip()))
            continue
        if not stripped:
            flush()
            continue
        paragraph.append(stripped)
    flush()
    return blocks


def blocks_from_plain_text(text: str) -> list[Block]:
    blocks: list[Block] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if CAPTION_RE.match(line) and len(line) <= 80:
            blocks.append(Block("caption", line))
        elif len(line) <= 40 and not re.search(r"[。；;，,.!?！？]$", line) and (
            TXT_HEADING_RE.match(line) or ABSTRACT_RE.match(line) or APPENDIX_RE.match(line)
            or CONCLUSION_RE.fullmatch(line)
        ):
            numbering = re.match(r"^\s*([0-9]+(?:\.[0-9]+)*)", line)
            level = numbering.group(1).count(".") + 1 if numbering else 1
            blocks.append(Block("heading", line, level))
        else:
            blocks.append(Block("para", line))
    return blocks


def _docx_style_names(archive: zipfile.ZipFile) -> dict[str, str]:
    try:
        root = ET.fromstring(archive.read("word/styles.xml"))
    except KeyError:
        return {}
    names = {}
    for style in root.iter(f"{W_NS}style"):
        style_id = style.get(f"{W_NS}styleId")
        name_el = style.find(f"{W_NS}name")
        if style_id and name_el is not None:
            names[style_id] = (name_el.get(f"{W_NS}val") or "").lower()
    return names


def _heading_level(style_name: str, outline_level: str | None) -> int:
    if outline_level is not None and outline_level.isdigit():
        return int(outline_level) + 1
    match = re.search(r"(heading|标题)\s*([1-9])", style_name)
    if match:
        return int(match.group(2))
    return 0


def blocks_from_docx(path: Path) -> tuple[list[Block], str | None]:
    with zipfile.ZipFile(path) as archive:
        style_names = _docx_style_names(archive)
        root = ET.fromstring(archive.read("word/document.xml"))
    blocks: list[Block] = []
    title = None
    for paragraph in root.iter(f"{W_NS}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{W_NS}t")).strip()
        if not text:
            continue
        style_id, outline_level = None, None
        ppr = paragraph.find(f"{W_NS}pPr")
        if ppr is not None:
            style_el = ppr.find(f"{W_NS}pStyle")
            if style_el is not None:
                style_id = style_el.get(f"{W_NS}val")
            outline_el = ppr.find(f"{W_NS}outlineLvl")
            if outline_el is not None:
                outline_level = outline_el.get(f"{W_NS}val")
        style_name = style_names.get(style_id or "", (style_id or "").lower())
        if style_name in {"title", "标题"} and title is None:
            title = text
            continue
        if style_name in {"caption", "题注"} or (CAPTION_RE.match(text) and len(text) <= 80):
            blocks.append(Block("caption", text))
            continue
        level = _heading_level(style_name, outline_level)
        if 0 < level <= 9:
            blocks.append(Block("heading", text, level))
        else:
            blocks.append(Block("para", text))
    return blocks, title


def blocks_from_pdf(path: Path) -> list[Block]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("读取 PDF 需要可选依赖 pypdf：pip install pypdf") from exc
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return blocks_from_plain_text(text)


def _section_text(blocks: list[Block], start: int) -> str:
    parts = []
    for block in blocks[start + 1:]:
        if block.kind == "heading":
            break
        if block.kind == "para":
            parts.append(block.text)
    return " ".join(parts)


def _count_units(blocks: list[Block]) -> int:
    text = " ".join(b.text for b in blocks)
    cjk = len(re.findall(r"[一-鿿]", text))
    words = len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text))
    return cjk + words


def build_view(blocks: list[Block], *, source: str, kind: str, title: str | None = None,
               abstract_chars: int = 300, conclusion_chars: int = 300) -> SkimView:
    view = SkimView(source=source, kind=kind)
    headings = [(i, b) for i, b in enumerate(blocks) if b.kind == "heading"]

    if title is None:
        top = [b for _, b in headings if b.level == 1]
        if top and not ABSTRACT_RE.match(top[0].text):
            title = top[0].text
        elif blocks:
            title = blocks[0].text
    view.title = _clip(title, 120) if title else None

    for index, block in headings:
        if ABSTRACT_RE.match(block.text):
            view.abstract = _clip(_section_text(blocks, index), abstract_chars) or None
            break
    if view.abstract is None:
        for block in blocks:
            if block.kind == "para" and ABSTRACT_RE.match(block.text):
                body = re.sub(r"^\S+?\s*[:：]\s*", "", block.text, count=1)
                view.abstract = _clip(body, abstract_chars)
                break

    appendix_started = False
    for index, block in enumerate(blocks):
        if block.kind == "heading":
            if APPENDIX_RE.match(block.text):
                appendix_started = True
                view.appendix_headings.append(block.text)
            elif block.level == 1 and appendix_started and not APPENDIX_RE.match(block.text):
                appendix_started = False
            view.outline.append({"level": block.level, "text": _clip(block.text, 80)})
            # 取最后一个匹配的章节，避免把中间各节的“小结”当成全文结论。
            if CONCLUSION_RE.search(block.text) and not appendix_started:
                view.conclusion = _clip(_section_text(blocks, index), conclusion_chars) or view.conclusion
        elif block.kind == "caption":
            view.captions.append(_clip(block.text, 100))
        elif block.kind == "para" and not appendix_started:
            view.appendix_refs_in_body += len(BODY_APPENDIX_REF_RE.findall(block.text))

    view.stats = {
        "text_units": _count_units(blocks),
        "headings": len(view.outline),
        "captions": len(view.captions),
        "paragraphs": sum(1 for b in blocks if b.kind == "para"),
    }
    _add_document_flags(view)
    return view


def _add_document_flags(view: SkimView) -> None:
    if view.abstract is None:
        view.flags.append("未找到摘要或简介：老师可能无法在开头看到目标和主要结果。")
    if view.conclusion is None:
        view.flags.append("未找到结论或总结章节：主要发现可能不容易被快速定位。")
    if len(view.outline) < 3:
        view.flags.append("标题少于 3 个：结构在快速浏览时可能不清楚。")
    if view.appendix_headings and view.appendix_refs_in_body == 0:
        view.flags.append("存在附录，但正文中没有找到对附录的引用：附录中的工作可能不会被看到。")


def skim_project(directory: Path, **kwargs) -> SkimView:
    readme = next(
        (p for p in sorted(directory.iterdir()) if p.is_file() and p.stem.lower() == "readme"),
        None,
    )
    if readme is not None:
        text = _read_text(readme)
        blocks = blocks_from_markdown(text) if readme.suffix.lower() in {".md", ".markdown", ""} else blocks_from_plain_text(text)
        view = build_view(blocks, source=str(directory), kind="project", **kwargs)
        # README 通常没有“摘要/结论”章节，这两条提示对项目不适用。
        view.flags = [f for f in view.flags if "摘要" not in f and "结论" not in f]
    else:
        view = SkimView(source=str(directory), kind="project", title=directory.name)
        view.flags.append("项目根目录没有 README：老师打开仓库时看不到项目目标和运行方式。")

    source_counts: dict[str, int] = {}
    test_files = 0
    for path in directory.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(directory).parts):
            continue
        if not path.is_file():
            continue
        if path.suffix in SOURCE_SUFFIXES:
            source_counts[path.suffix] = source_counts.get(path.suffix, 0) + 1
        lowered = path.name.lower()
        if lowered.startswith("test") or lowered.endswith(("_test.py", ".test.js", ".test.ts", ".spec.js", ".spec.ts", "test.java")):
            test_files += 1

    top_level = sorted(
        p.name + ("/" if p.is_dir() else "")
        for p in directory.iterdir()
        if p.name not in IGNORED_DIRS and not p.name.startswith(".")
    )
    manifests = [name for name in (
        "requirements.txt", "pyproject.toml", "setup.py", "environment.yml", "package.json",
        "pom.xml", "build.gradle", "CMakeLists.txt", "Makefile", "Cargo.toml", "go.mod", "Dockerfile",
    ) if (directory / name).exists()]
    has_run_hint = any(RUN_HINT_RE.search(item["text"]) for item in view.outline)

    view.project = {
        "readme": readme.name if readme else None,
        "top_level": top_level[:40],
        "source_files_by_suffix": dict(sorted(source_counts.items())),
        "test_files": test_files,
        "dependency_manifests": manifests,
        "readme_has_run_section": has_run_hint,
    }
    if readme is not None and not has_run_hint:
        view.flags.append("README 中没有找到安装/运行/使用相关章节：老师可能无法快速运行项目。")
    if test_files == 0:
        view.flags.append("没有找到测试文件：若评分涉及正确性或代码质量，测试证据可能不可见。")
    if source_counts and not manifests:
        view.flags.append("没有找到依赖清单（如 requirements.txt、package.json）：运行环境可能无法复现。")
    return view


def skim_path(path: Path, **kwargs) -> SkimView:
    if path.is_dir():
        return skim_project(path, **kwargs)
    suffix = path.suffix.lower()
    title = None
    if suffix in {".md", ".markdown"}:
        blocks, kind = blocks_from_markdown(_read_text(path)), "markdown"
    elif suffix == ".txt":
        blocks, kind = blocks_from_plain_text(_read_text(path)), "text"
    elif suffix == ".docx":
        (blocks, title), kind = blocks_from_docx(path), "docx"
    elif suffix == ".pdf":
        blocks, kind = blocks_from_pdf(path), "pdf"
    else:
        raise ValueError(f"不支持的文件类型：{suffix or '(无扩展名)'}；支持 .md .txt .docx .pdf 或项目目录")
    return build_view(blocks, source=str(path), kind=kind, title=title, **kwargs)


def render_markdown(view: SkimView) -> str:
    lines = [
        "# 30 秒视图（启发式抽取，不代表真实阅卷方式）",
        "",
        f"- 来源：`{Path(view.source).name}`（{view.kind}）",
        f"- 标题：{view.title or '（未识别）'}",
        "",
        "## 摘要 / 简介",
        view.abstract or "（未找到）",
        "",
        "## 标题结构",
    ]
    if view.outline:
        lines += [f"{'  ' * (max(item['level'], 1) - 1)}- {item['text']}" for item in view.outline]
    else:
        lines.append("（未识别到标题）")
    lines += ["", "## 图表标题"]
    lines += [f"- {c}" for c in view.captions] or ["（未找到）"]
    lines += ["", "## 结论 / 总结", view.conclusion or "（未找到）", "", "## 附录与引用"]
    if view.appendix_headings:
        lines.append(f"- 附录章节：{'、'.join(view.appendix_headings)}")
        lines.append(f"- 正文中提到附录的次数：{view.appendix_refs_in_body}")
    else:
        lines.append("- 未识别到附录章节")
    if view.project is not None:
        project = view.project
        lines += [
            "",
            "## 项目结构",
            f"- README：{project['readme'] or '无'}",
            f"- 顶层条目：{'、'.join(project['top_level']) or '（空）'}",
            f"- 源代码文件：{', '.join(f'{k} ×{v}' for k, v in project['source_files_by_suffix'].items()) or '无'}",
            f"- 测试文件数：{project['test_files']}",
            f"- 依赖清单：{'、'.join(project['dependency_manifests']) or '无'}",
        ]
    stats = view.stats
    if stats:
        lines += [
            "",
            "## 统计",
            f"- 字数（汉字 + 英文单词）：{stats['text_units']}；标题 {stats['headings']} 个；"
            f"图表标题 {stats['captions']} 个；段落 {stats['paragraphs']} 个",
        ]
    lines += ["", "## 可见性提示（非阻断）"]
    lines += [f"- {flag}" for flag in view.flags] or ["- 未发现结构层面的可见性提示。"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成作业的 30 秒视图（GPAO 可见性检查用）")
    parser.add_argument("path", help="作业文件（.md/.txt/.docx/.pdf）或项目目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON 而不是 Markdown")
    parser.add_argument("--abstract-chars", type=int, default=300)
    parser.add_argument("--conclusion-chars", type=int, default=300)
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    path = Path(args.path)
    if not path.exists():
        print(f"错误：路径不存在：{path}", file=sys.stderr)
        return 2
    try:
        view = skim_path(path, abstract_chars=args.abstract_chars, conclusion_chars=args.conclusion_chars)
    except (ValueError, RuntimeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(asdict(view), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(view), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
