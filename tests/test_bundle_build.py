import unittest
import os
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / 'dist'
TOOLS_DIR = ROOT / 'tools'

class TestBundleBuild(unittest.TestCase):
    def test_bundle_is_up_to_date_and_clean(self):
        """测试 Bundle 是否基于源码确定性一致，并且不包含非法字面量"""
        manifest_path = DIST_DIR / 'bundle_manifest.json'
        bundle_path = DIST_DIR / 'GPAO.bundle.md'
        
        self.assertTrue(manifest_path.exists(), "Manifest file missing. Please build bundle first.")
        self.assertTrue(bundle_path.exists(), "Bundle file missing. Please build bundle first.")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            current_manifest = json.load(f)
        
        # 1. 重构测试，不触碰真实 dist，只在内存和临时目录工作
        import sys
        sys.path.insert(0, str(TOOLS_DIR))
        from build_bundle import render_bundle, write_bundle
        
        final_content, manifest_data = render_bundle()
        
        # 2. 对比 source_set_sha256 是否一致
        self.assertEqual(
            current_manifest.get('source_set_sha256'), 
            manifest_data['source_set_sha256'], 
            "The existing bundle is outdated! Source files have changed. Please run tools/build_bundle.py before committing."
        )
        
        # 3. 对比 bundle_sha256 是否一致
        self.assertEqual(
            current_manifest.get('bundle_sha256'),
            manifest_data['bundle_sha256'],
            "The existing bundle hash mismatch! Bundle determinism broke."
        )
        
        # 4. 测试临时写盘
        with tempfile.TemporaryDirectory() as tempdir:
            self.assertTrue(write_bundle(tempdir), "Failed to write bundle to temp dir.")
            
        # 5. 断言没有非法的字面量 \n\n 出现
        # 上一版 build_bundle.py 中错误地使用了 "\\n\\n"
        self.assertNotIn(r"\n\n", final_content, r"Bundle contains literal \n\n instead of actual newlines.")
        
if __name__ == '__main__':
    unittest.main()
