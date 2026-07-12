import unittest
import os
import sys
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / 'tools'))

from ci_checker import (
    TEXT_GLOBS,
    check_json_syntax,
    check_markdown_links,
    check_python_syntax,
    check_tracked_private_files,
    check_utf8_and_mojibake,
)

class TestRepositoryIntegrity(unittest.TestCase):
    def test_utf8_and_mojibake(self):
        for ext in TEXT_GLOBS:
            for file_path in ROOT.rglob(ext):
                if '.git' in str(file_path):
                    continue
                ok, msg = check_utf8_and_mojibake(file_path)
                self.assertTrue(ok, f"{file_path.relative_to(ROOT)}: {msg}")

    def test_python_syntax(self):
        for file_path in ROOT.rglob('*.py'):
            if '.git' in str(file_path):
                continue
            ok, msg = check_python_syntax(file_path)
            self.assertTrue(ok, f"{file_path.relative_to(ROOT)}: {msg}")

    def test_markdown_links(self):
        link_errors = check_markdown_links()
        self.assertEqual(len(link_errors), 0, "\\n".join(link_errors))

    def test_json_and_jsonl_syntax(self):
        for ext in ('*.json', '*.jsonl'):
            for file_path in ROOT.rglob(ext):
                if '.git' in str(file_path):
                    continue
                ok, msg = check_json_syntax(file_path)
                self.assertTrue(ok, f"{file_path.relative_to(ROOT)}: {msg}")

    def test_private_material_is_not_tracked(self):
        errors = check_tracked_private_files()
        self.assertEqual(errors, [], "\\n".join(errors))

    @mock.patch("ci_checker.subprocess.run")
    def test_raw_evaluation_artifacts_are_rejected_if_tracked(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = "evals/raw/model-output.md\n"
        run.return_value.stderr = ""
        self.assertEqual(
            check_tracked_private_files(),
            ["Tracked private file: evals/raw/model-output.md"],
        )

if __name__ == '__main__':
    unittest.main()
