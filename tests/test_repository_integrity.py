import unittest
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / 'tools'))

from ci_checker import check_utf8_and_mojibake, check_python_syntax, check_markdown_links

class TestRepositoryIntegrity(unittest.TestCase):
    def test_utf8_and_mojibake(self):
        for ext in ['*.md', '*.py']:
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

if __name__ == '__main__':
    unittest.main()
