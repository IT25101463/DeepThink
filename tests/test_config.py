"""
Unit tests for configuration and directory paths.
"""

import unittest
from pathlib import Path
from src.config import PROJECT_ROOT, DATA_DIR, EXTRACTED_MEDIA_DIR


class TestConfig(unittest.TestCase):
    def test_project_paths(self):
        self.assertTrue(PROJECT_ROOT.exists(), "PROJECT_ROOT should exist")
        self.assertTrue(DATA_DIR.exists(), "DATA_DIR should exist")
        self.assertTrue(EXTRACTED_MEDIA_DIR.exists(), "EXTRACTED_MEDIA_DIR should exist")
        self.assertTrue((EXTRACTED_MEDIA_DIR / "figures").exists(), "figures directory should exist")
        self.assertTrue((EXTRACTED_MEDIA_DIR / "tables").exists(), "tables directory should exist")


if __name__ == "__main__":
    unittest.main()
