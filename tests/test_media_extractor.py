"""
Unit tests for Media Extraction Module (Member P2).
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from src.config import PROJECT_ROOT, CORPUS_DIR, EXTRACTED_MEDIA_DIR
from src.ingestion.media_extractor import (
    extract_images_from_pdf,
    extract_standalone_images,
    _describe_wiki_image,
    _match_known_plate,
    KNOWN_CODEX_PLATES
)
from src.utils.schema_validator import validate_chunk


class TestMediaExtractor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_known_codex_plates_matching(self):
        match = _match_known_plate("plate_08_creature_weeping_lurker")
        self.assertIsNotNone(match)
        self.assertIn("Weeping Lurker", match["entity"])
        self.assertIn("3 of 10", match["content"])

        match_none = _match_known_plate("unknown_random_image")
        self.assertIsNone(match_none)

    def test_describe_wiki_image(self):
        desc = _describe_wiki_image("atmo_heraldry_faction_house_morvain.png")
        self.assertIn("Crossed Golden Keys", desc["caption"])
        self.assertIn("House Morvain", desc["entities"])

        desc_ignatz = _describe_wiki_image("atmo_portrait_character_ignatz_ashgrove_the_oathless.png")
        self.assertIn("Parchment Scroll", desc_ignatz["caption"])

        desc_gauntlet = _describe_wiki_image("atmo_relic_artifact_gauntlet_of_sorrowfell.png")
        self.assertIn("Coiled Serpent", desc_gauntlet["caption"])

    def test_extract_images_from_sample_pdf(self):
        # Use a real archive PDF containing embedded figure plates
        sample_pdf = CORPUS_DIR / "codex" / "codex_vaeloria_ii_armory_of_relics_and_bestiary.pdf"
        if not sample_pdf.exists():
            self.skipTest(f"Sample PDF not found: {sample_pdf}")

        output_dir = self.temp_dir / "figures"
        chunks = extract_images_from_pdf(sample_pdf, output_dir)

        self.assertGreater(len(chunks), 0, "Should extract figure plates from codex PDF")
        for chunk in chunks:
            self.assertEqual(chunk["modality"], "image-caption")
            self.assertIn("dimensions", chunk["metadata"])
            self.assertGreaterEqual(chunk["metadata"]["dimensions"][0], 100)
            self.assertGreaterEqual(chunk["metadata"]["dimensions"][1], 100)

            # Check file exists on disk
            full_media_path = PROJECT_ROOT / chunk["media_path"]
            self.assertTrue(full_media_path.exists(), f"Media file must exist: {full_media_path}")

            # Validate against schema contract
            errs = validate_chunk(chunk, PROJECT_ROOT)
            self.assertEqual(len(errs), 0, f"Chunk {chunk['chunk_id']} has schema errors: {errs}")

    def test_extract_standalone_images(self):
        if not CORPUS_DIR.exists():
            self.skipTest(f"Corpus directory not found: {CORPUS_DIR}")

        output_dir = self.temp_dir / "figures"
        chunks = extract_standalone_images(CORPUS_DIR, output_dir)

        self.assertGreater(len(chunks), 0, "Should ingest standalone archive images")
        for chunk in chunks[:10]:
            self.assertEqual(chunk["modality"], "image-caption")
            self.assertTrue(chunk["content"])
            self.assertTrue(chunk["caption"])
            full_media_path = PROJECT_ROOT / chunk["media_path"]
            self.assertTrue(full_media_path.exists(), f"Media file must exist: {full_media_path}")
            errs = validate_chunk(chunk, PROJECT_ROOT)
            self.assertEqual(len(errs), 0, f"Chunk {chunk['chunk_id']} has schema errors: {errs}")


if __name__ == "__main__":
    unittest.main()

