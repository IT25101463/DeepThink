"""
Unit tests for Document Parser (Member P1).
"""

import unittest
from pathlib import Path
import tempfile

from src.ingestion.parser import (
    sanitize_id,
    assign_source_reliability,
    detect_document_type,
    hierarchical_chunk,
    parse_markdown_file,
    parse_txt_file,
    parse_document,
)
from src.utils.schema_validator import validate_chunk


class TestParser(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent

    def test_sanitize_id(self):
        self.assertEqual(sanitize_id("Codex Imperial: Vol 1 (Final!)"), "codex_imperial_vol_1_final")
        self.assertEqual(sanitize_id(""), "chunk")

    def test_assign_source_reliability(self):
        self.assertEqual(assign_source_reliability(Path("data/codex/volume_1.pdf")), "official_codex")
        self.assertEqual(assign_source_reliability(Path("data/wiki/marrowwatch.md")), "wiki")
        self.assertEqual(assign_source_reliability(Path("data/chronicles/book_1.docx")), "novel")
        self.assertEqual(assign_source_reliability(Path("data/ephemera/court_martial_01.pdf")), "ephemera_trial")
        self.assertEqual(assign_source_reliability(Path("data/ephemera/ballad_cinders.docx")), "ephemera_tavern")
        self.assertEqual(assign_source_reliability(Path("data/ephemera/auction_catalogue.txt")), "ephemera_catalogue")

    def test_detect_document_type(self):
        self.assertEqual(detect_document_type(Path("ballad.scan.pdf")), "scan")
        self.assertEqual(detect_document_type(Path("doc.pdf")), "pdf")
        self.assertEqual(detect_document_type(Path("notes.docx")), "docx")
        self.assertEqual(detect_document_type(Path("lore.md")), "md")
        self.assertEqual(detect_document_type(Path("ledger.txt")), "txt")

    def test_hierarchical_chunk_schema(self):
        sample_text = (
            "The Ashen Era marked the sundering of the Northern reaches. "
            "High towers fell before the rising cinder storms. "
            "Scholars of the White Spire catalogued thirty relics."
        )
        chunks = hierarchical_chunk(
            text=sample_text,
            doc_name="test_lore.md",
            doc_type="md",
            page_num=1,
            section_title="The Fall of the North",
            base_metadata={"source_reliability": "wiki"}
        )
        self.assertGreaterEqual(len(chunks), 1)
        chunk = chunks[0]
        
        # Verify schema validity
        errs = validate_chunk(chunk, self.project_root)
        self.assertEqual(len(errs), 0, f"Chunk failed schema validation: {errs}")
        self.assertEqual(chunk["modality"], "text")
        self.assertEqual(chunk["metadata"]["source_reliability"], "wiki")

    def test_markdown_parser_hierarchical_headers(self):
        md_content = """# Marrowwatch Citadel

Marrowwatch was constructed during the early Kindling Years.

## The Great Cistern

The subterranean cistern held three thousand barrels of mountain runoff.

### Defense Grid

The outer wall was reinforced with ash-iron plates.
"""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(md_content)
            temp_path = Path(f.name)

        try:
            chunks = parse_markdown_file(temp_path)
            self.assertGreaterEqual(len(chunks), 2)
            
            # Check compound section title preservation
            titles = [c["section_title"] for c in chunks]
            self.assertTrue(any("Great Cistern" in t for t in titles))
            
            # Check chunk schema
            for c in chunks:
                errs = validate_chunk(c, self.project_root)
                self.assertEqual(len(errs), 0, f"Markdown chunk invalid: {errs}")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_txt_parser(self):
        txt_content = """AUCTION CATALOGUE: ITEM 42
Relic Name: The Cinder-Wrought Aegis
Estimated Value: 500 gold sovereigns
Current Custodian: Master Halvard of Sablewood
"""
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(txt_content)
            temp_path = Path(f.name)

        try:
            chunks = parse_txt_file(temp_path)
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0]["document_type"], "txt")
            self.assertIn("AUCTION CATALOGUE", chunks[0]["section_title"])
            
            errs = validate_chunk(chunks[0], self.project_root)
            self.assertEqual(len(errs), 0)
        finally:
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
