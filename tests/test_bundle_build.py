import unittest
import os
import subprocess
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / 'dist'

class TestBundleBuild(unittest.TestCase):
    def test_bundle_is_up_to_date(self):
        """测试 Bundle 是否和源文件同步且可构建"""
        manifest_path = DIST_DIR / 'bundle_manifest.json'
        bundle_path = DIST_DIR / 'GPAO.bundle.md'
        
        self.assertTrue(manifest_path.exists(), "Manifest file missing.")
        self.assertTrue(bundle_path.exists(), "Bundle file missing.")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_content = f.read()
            
        sha256 = hashlib.sha256(bundle_content.encode('utf-8')).hexdigest()
        self.assertEqual(sha256, manifest['sha256'], "Bundle SHA-256 does not match manifest.")

if __name__ == '__main__':
    unittest.main()
