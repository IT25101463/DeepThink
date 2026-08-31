"""
Unit tests for Table Extraction Module (Member P2).
"""

import unittest
from pathlib import Path

from src.config import PROJECT_ROOT, CORPUS_DIR
from src.ingestion.table_extractor import format_markdown_table, extract_tables_from_pdf
from src.utils.schema_validator import validate_chunk


class TestTableExtractor(unittest.TestCase):
    def test_format_markdown_table_multi_row(self):
        table_data = [
            ["Item", "Cost", "Location"],
            ["Chalice of Ashdeep", "27 vitae", "Crookgate Keep"],
            ["The Thrice-Bound Edge", "94 vitae", "Crookvale\n(Hollowreach)"]
        ]
        md = format_markdown_table(table_data)
        lines = md.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertIn("| Item | Cost | Location |", lines[0])
        self.assertIn("| --- | --- | --- |", lines[1])
        self.assertIn("Chalice of Ashdeep", lines[2])
        self.assertIn("Crookvale (Hollowreach)", lines[3])

    def test_format_markdown_table_single_row(self):
        table_data = [
            ["Environmental pressure", "Ash, water, and unstable marsh ground"]
        ]
        md = format_markdown_table(table_data)
        lines = md.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("| Property | Record |", lines[0])
        self.assertIn("Environmental pressure", lines[2])

    def test_format_markdown_table_empty(self):
        self.assertEqual(format_markdown_table([]), "")
        self.assertEqual(format_markdown_table([[None, None]]), "")

    def test_extract_tables_from_sample_pdf(self):
        sample_pdf = CORPUS_DIR / "codex" / "codex_vaeloria_i_gazetteer_of_the_sundered_realms.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF not found: {sample_pdf}")

        chunks = extract_tables_from_pdf(sample_pdf)
        self.assertGreater(len(chunks), 0, "Should extract tables from codex PDF")

        for chunk in chunks:
            self.assertEqual(chunk["modality"], "table")
            self.assertIn("table_dimensions", chunk["metadata"])
            self.assertGreaterEqual(chunk["metadata"]["table_dimensions"][0], 1)
            self.assertTrue(chunk["content"].startswith("|"))
            errs = validate_chunk(chunk, PROJECT_ROOT)
            self.assertEqual(len(errs), 0, f"Table chunk {chunk['chunk_id']} failed validation: {errs}")

    def test_extract_tables_from_ledger_pdf(self):
        sample_pdf = CORPUS_DIR / "ephemera" / "quartermaster_ledger_concerning_bryony_nightbrook.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF not found: {sample_pdf}")

        chunks = extract_tables_from_pdf(sample_pdf)
        self.assertGreater(len(chunks), 0, "Should extract tables from quartermaster ledger PDF")
        for chunk in chunks:
            self.assertEqual(chunk["modality"], "table")
            errs = validate_chunk(chunk, PROJECT_ROOT)
            self.assertEqual(len(errs), 0)


if __name__ == "__main__":
    unittest.main()

