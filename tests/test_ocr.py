"""
Unit tests for OCR Engine (Member P1).
"""

import unittest
from pathlib import Path
from PIL import Image, ImageDraw

from src.ingestion.ocr_engine import (
    preprocess_image_for_ocr,
    run_ocr_on_image,
    find_tesseract_binary,
    init_tesseract,
)


class TestOCREngine(unittest.TestCase):
    def setUp(self):
        # Create a synthetic image with high contrast text
        self.img = Image.new("RGB", (300, 100), color=(240, 230, 200))
        d = ImageDraw.Draw(self.img)
        d.text((10, 10), "TEST ARCHIVE 101", fill=(20, 20, 20))

    def test_preprocess_image_for_ocr(self):
        processed = preprocess_image_for_ocr(self.img, upscale_min_width=600)
        # Should be binarized ('1' mode or 'L' mode)
        self.assertIn(processed.mode, ("1", "L"))
        # Should be upscaled
        self.assertGreaterEqual(processed.size[0], 600)

    def test_find_tesseract_binary_type(self):
        result = find_tesseract_binary()
        self.assertTrue(result is None or isinstance(result, str))

    def test_run_ocr_graceful_fallback(self):
        # Verify that run_ocr_on_image does not raise exceptions even if Tesseract is missing
        text = run_ocr_on_image(self.img, preprocess=True)
        self.assertIsInstance(text, str)


if __name__ == "__main__":
    unittest.main()
