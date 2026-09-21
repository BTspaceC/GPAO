# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "tools"))

import install_skill  # noqa: E402


class TestInstallSkill(unittest.TestCase):
    def test_manifest_contains_runtime_files_only(self):
        files = install_skill.runtime_manifest()
        self.assertIn("SKILL.md", files)
        self.assertIn("workflows/quick_audit.md", files)
        self.assertIn("tools/skim_view.py", files)
        for rel in files:
            self.assertTrue((ROOT / rel).exists(), rel)
            self.assertFalse(rel.startswith(("tests/", "evals/", "dist/", "test_runs/")), rel)

    def test_every_path_referenced_by_runtime_markdown_is_installed(self):
        files = set(install_skill.runtime_manifest())
        import re
        pattern = re.compile(r"`(?:\.\./)?((?:workflows|adapters|templates|tools)/[^`\s]+\.(?:md|py))`")
        for rel in files:
            if not rel.endswith(".md"):
                continue
            for ref in pattern.findall((ROOT / rel).read_text(encoding="utf-8")):
                self.assertIn(ref, files, f"{rel} references {ref}, which is not installed")

    def test_install_copies_files_and_refuses_foreign_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "gpao"
            files = install_skill.install(dest)
            for rel in files:
                self.assertTrue((dest / rel).exists(), rel)
            self.assertTrue((dest / install_skill.MARKER).exists())
            install_skill.install(dest)  # reinstall over own install is allowed

            foreign = Path(tmp) / "other"
            foreign.mkdir()
            (foreign / "keep.txt").write_text("user file", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                install_skill.install(foreign)
            self.assertTrue((foreign / "keep.txt").exists())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "gpao"
            install_skill.install(dest, dry_run=True)
            self.assertFalse(dest.exists())

    def test_named_targets(self):
        self.assertEqual(install_skill.resolve_target("claude").parts[-3:], (".claude", "skills", "gpao"))
        self.assertEqual(install_skill.resolve_target("codex").name, "gpao")


if __name__ == "__main__":
    unittest.main()
