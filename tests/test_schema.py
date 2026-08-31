"""
Unit tests for data contract schema validation.
"""

import unittest
from pathlib import Path
from src.utils.schema_validator import validate_chunk, validate_chunks_file


class TestSchemaValidator(unittest.TestCase):
    def test_valid_chunk_validation(self):
        root = Path(__file__).resolve().parent.parent
        valid_chunk = {
            "chunk_id": "test_chunk_01",
            "document_name": "Test_Doc.pdf",
            "document_type": "pdf",
            "page_number": 1,
            "section_title": "Introduction",
            "modality": "text",
            "content": "This is a valid test chunk content.",
            "media_path": None,
            "caption": None,
            "metadata": {"word_count": 7}
        }
        errors = validate_chunk(valid_chunk, root)
        self.assertEqual(len(errors), 0, f"Valid chunk should have 0 errors, got: {errors}")

    def test_invalid_chunk_detection(self):
        root = Path(__file__).resolve().parent.parent
        invalid_chunk = {
            "chunk_id": "bad_01",
            "document_name": "test.pdf",
            "document_type": "invalid_type",
            "page_number": 1,
            "section_title": "Test",
            "modality": "unknown_modality",
            "content": ""
        }
        errors = validate_chunk(invalid_chunk, root)
        self.assertGreater(len(errors), 0, "Validator should flag invalid chunk")


if __name__ == "__main__":
    unittest.main()
