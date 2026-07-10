import unittest
import os
import subprocess
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / 'dist'
TOOLS_DIR = ROOT / 'tools'

class TestBundleBuild(unittest.TestCase):
    def test_bundle_is_up_to_date(self):
        """测试 Bundle 是否和源文件同步且可构建"""
        manifest_path = DIST_DIR / 'bundle_manifest.json'
        bundle_path = DIST_DIR / 'GPAO.bundle.md'
        
        self.assertTrue(manifest_path.exists(), "Manifest file missing. Please build bundle first.")
        self.assertTrue(bundle_path.exists(), "Bundle file missing. Please build bundle first.")
        
        with open(bundle_path, 'r', encoding='utf-8') as f:
            current_bundle_content = f.read()
            
        current_sha256 = hashlib.sha256(current_bundle_content.encode('utf-8')).hexdigest()
        
        # 在临时目录重新构建一次，对比内容
        with tempfile.TemporaryDirectory() as tempdir:
            temp_bundle_path = Path(tempdir) / 'test_bundle.md'
            
            # 使用 tools/build_bundle.py 中定义的逻辑
            import sys
            sys.path.insert(0, str(TOOLS_DIR))
            from build_bundle import build_bundle
            
            # Monkeypatch the bundle path for testing
            import build_bundle as bb
            bb.BUNDLE_PATH = temp_bundle_path
            
            # Run the build
            result = bb.build_bundle()
            self.assertTrue(result, "Failed to rebuild bundle dynamically.")
            
            with open(temp_bundle_path, 'r', encoding='utf-8') as f:
                new_bundle_content = f.read()
            
            new_sha256 = hashlib.sha256(new_bundle_content.encode('utf-8')).hexdigest()
            
            # 这一步对比要求 `build_bundle.py` 必须是确定性的 (无动态 datetime)
            self.assertEqual(current_sha256, new_sha256, "The existing bundle is outdated! Please run tools/build_bundle.py before committing.")

if __name__ == '__main__':
    unittest.main()
