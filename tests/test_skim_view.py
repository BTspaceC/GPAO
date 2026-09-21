# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "tools"))

import skim_view  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

MARKDOWN = """# 耳机使用与听觉疲劳的关系调查

## 摘要
本文调查了大学生耳机使用时长与主观听觉疲劳的关系。

## 1 方法
问卷见附录A。

![图1 使用时长分布](figure.png)

### 1.1 小结
这是中间小节的小结。

## 2 结论
使用时长与疲劳评分相关，但不能推出因果。

## 附录A 问卷
问卷原文。
"""


def _para(text, style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}<w:r><w:t>{text}</w:t></w:r></w:p>"


def make_docx(path: Path, paragraphs):
    body = "".join(_para(text, style) for text, style in paragraphs)
    document = f"<w:document {W}><w:body>{body}</w:body></w:document>"
    styles = (
        f"<w:styles {W}>"
        '<w:style w:styleId="1"><w:name w:val="heading 1"/></w:style>'
        '<w:style w:styleId="2"><w:name w:val="heading 2"/></w:style>'
        '<w:style w:styleId="Title"><w:name w:val="Title"/></w:style>'
        '<w:style w:styleId="Caption"><w:name w:val="caption"/></w:style>'
        "</w:styles>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)


class TestSkimViewDocuments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_markdown_extracts_all_skim_sections(self):
        path = self.dir / "paper.md"
        path.write_text(MARKDOWN, encoding="utf-8")
        view = skim_view.skim_path(path)
        self.assertEqual(view.title, "耳机使用与听觉疲劳的关系调查")
        self.assertIn("耳机使用时长", view.abstract)
        self.assertEqual(view.captions, ["图1 使用时长分布"])
        self.assertIn("不能推出因果", view.conclusion)
        self.assertEqual(view.appendix_headings, ["附录A 问卷"])
        self.assertEqual(view.appendix_refs_in_body, 1)
        self.assertEqual(view.flags, [])

    def test_last_conclusion_heading_wins_over_section_summaries(self):
        path = self.dir / "paper.md"
        path.write_text(MARKDOWN, encoding="utf-8")
        view = skim_view.skim_path(path)
        self.assertNotIn("中间小节", view.conclusion)

    def test_unreferenced_appendix_and_missing_sections_are_flagged(self):
        path = self.dir / "draft.md"
        path.write_text("# 标题\n\n正文一段。\n\n## 附录\n材料。\n", encoding="utf-8")
        flags = "\n".join(skim_view.skim_path(path).flags)
        self.assertIn("未找到摘要", flags)
        self.assertIn("未找到结论", flags)
        self.assertIn("正文中没有找到对附录的引用", flags)

    def test_plain_text_headings_and_captions(self):
        path = self.dir / "report.txt"
        path.write_text(
            "实验报告\n摘要\n本实验测量了重力加速度。\n一、实验原理\n单摆周期公式。\n"
            "表1 测量数据\n五、结论\n测得结果与理论值接近。\n",
            encoding="utf-8",
        )
        view = skim_view.skim_path(path)
        self.assertEqual(view.title, "实验报告")
        self.assertIn("重力加速度", view.abstract)
        self.assertIn("表1 测量数据", view.captions)
        self.assertIn("理论值接近", view.conclusion)

    def test_gbk_text_is_decoded(self):
        path = self.dir / "gbk.txt"
        path.write_bytes("标题\n摘要\n中文内容。\n".encode("gbk"))
        self.assertIn("中文内容", skim_view.skim_path(path).abstract)

    def test_docx_uses_style_names_for_title_headings_and_captions(self):
        path = self.dir / "report.docx"
        make_docx(path, [
            ("课程报告", "Title"),
            ("摘要", "1"),
            ("本文研究了课程作业的可见性。", None),
            ("方法", "1"),
            ("数据来源", "2"),
            ("图1 流程", "Caption"),
            ("结论", "1"),
            ("主要工作在正文中可见。", None),
        ])
        view = skim_view.skim_path(path)
        self.assertEqual(view.title, "课程报告")
        self.assertIn("可见性", view.abstract)
        self.assertEqual([item["level"] for item in view.outline], [1, 1, 2, 1])
        self.assertEqual(view.captions, ["图1 流程"])
        self.assertIn("正文中可见", view.conclusion)

    def test_pdf_without_pypdf_reports_optional_dependency(self):
        path = self.dir / "a.pdf"
        path.write_bytes(b"%PDF-1.4")
        with mock.patch.dict(sys.modules, {"pypdf": None}):
            with self.assertRaisesRegex(RuntimeError, "pypdf"):
                skim_view.skim_path(path)

    def test_unsupported_extension_is_rejected(self):
        path = self.dir / "a.pptx"
        path.write_bytes(b"x")
        with self.assertRaises(ValueError):
            skim_view.skim_path(path)


class TestSkimViewProjects(unittest.TestCase):
    def test_project_without_run_section_tests_or_manifest_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "README.md").write_text("# 图书管理系统\n\n## 功能\n借书还书。\n", encoding="utf-8")
            (project / "src").mkdir()
            (project / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
            view = skim_view.skim_path(project)
            flags = "\n".join(view.flags)
            self.assertEqual(view.kind, "project")
            self.assertEqual(view.project["source_files_by_suffix"], {".py": 1})
            self.assertIn("安装/运行", flags)
            self.assertIn("没有找到测试文件", flags)
            self.assertIn("依赖清单", flags)
            self.assertNotIn("摘要", flags)

    def test_complete_project_has_no_project_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "README.md").write_text(
                "# 系统\n\n## 功能\n说明。\n\n## 运行方式\npython main.py\n", encoding="utf-8"
            )
            (project / "requirements.txt").write_text("", encoding="utf-8")
            (project / "main.py").write_text("", encoding="utf-8")
            (project / "tests").mkdir()
            (project / "tests" / "test_main.py").write_text("", encoding="utf-8")
            view = skim_view.skim_path(project)
            self.assertEqual(view.flags, [])
            self.assertEqual(view.project["test_files"], 1)

    def test_missing_readme_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            view = skim_view.skim_path(Path(tmp))
            self.assertIn("没有 README", "\n".join(view.flags))


class TestSkimViewCli(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / "skim_view.py"), *args],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

    def test_cli_markdown_and_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.md"
            path.write_text(MARKDOWN, encoding="utf-8")
            markdown = self._run(str(path))
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("30 秒视图", markdown.stdout)
            self.assertIn("不代表真实阅卷方式", markdown.stdout)
            as_json = self._run(str(path), "--json")
            self.assertEqual(as_json.returncode, 0, as_json.stderr)
            self.assertEqual(json.loads(as_json.stdout)["captions"], ["图1 使用时长分布"])

    def test_cli_missing_path_fails_cleanly(self):
        result = self._run("does-not-exist.md")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
