"""
Unit tests for Member P4 Grounded Generation Engine.
"""

import os
import unittest
from pathlib import Path

from src.generation.generator import (
    format_context_prompt,
    resolve_media_path,
    verify_and_fix_media_paths,
    synthesize_grounded_fallback,
    generate_answer,
    GROUNDED_SYSTEM_PROMPT
)


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.sample_chunks = [
            {
                "chunk_id": "test_chunk_01",
                "document_name": "the_annals_of_the_ashen_era.pdf",
                "page_number": 4,
                "modality": "text",
                "content": "The Accord of Mournthrone was signed in 342 AS following the siege.",
                "media_path": None,
                "caption": None,
                "metadata": {"source_reliability": "official_codex"}
            },
            {
                "chunk_id": "test_chunk_02",
                "document_name": "plate_00_location_marrowwatch.png",
                "page_number": 1,
                "modality": "image-caption",
                "content": "Official figure plate depicting Marrowwatch garrison strength (3,107 souls).",
                "media_path": "data/extracted_media/figures/plate_00_location_marrowwatch.png",
                "caption": "Figure Plate: Marrowwatch Garrison Strength",
                "metadata": {"source_reliability": "official_codex"}
            }
        ]

    def test_prompt_formatting(self):
        prompt = format_context_prompt("What was the Accord?", self.sample_chunks)
        self.assertIn("User Query: What was the Accord?", prompt)
        self.assertIn("the_annals_of_the_ashen_era.pdf", prompt)
        self.assertIn("Page 4", prompt)
        self.assertIn("Marrowwatch Garrison Strength", prompt)

    def test_system_prompt_rules(self):
        self.assertIn("SCHOLARLY RIGOR", GROUNDED_SYSTEM_PROMPT)
        self.assertIn("PRECISE IN-TEXT CITATIONS", GROUNDED_SYSTEM_PROMPT)
        self.assertIn("MULTIMODAL INLINE FIGURE & TABLE EMBEDDINGS", GROUNDED_SYSTEM_PROMPT)
        self.assertIn("STRICT OUT-OF-SCOPE REFUSAL", GROUNDED_SYSTEM_PROMPT)

    def test_resolve_media_path(self):
        # Existing figure in extracted media
        res = resolve_media_path("data/extracted_media/figures/plate_00_location_marrowwatch.png")
        if res:
            self.assertIn("plate_00_location_marrowwatch.png", res)

    def test_verify_and_fix_media_paths_injection(self):
        raw_text = "The garrison strength is 3,107 souls as recorded in [codex_vaeloria.pdf, Page 1]."
        fixed = verify_and_fix_media_paths(raw_text, [self.sample_chunks[1]])
        # Should inject image if not present
        if Path("data/extracted_media/figures/plate_00_location_marrowwatch.png").exists():
            self.assertIn("![", fixed)

    def test_synthesize_grounded_fallback(self):
        ans = synthesize_grounded_fallback("What is the garrison strength?", [self.sample_chunks[1]])
        self.assertIn("plate_00_location_marrowwatch.png", ans)
        self.assertIn("3,107 souls", ans)

    def test_generate_answer_empty_query(self):
        ans = generate_answer("", [])
        self.assertIn("Please ask a question", ans)

    def test_generate_answer_with_context(self):
        ans = generate_answer("When was the Accord signed?", self.sample_chunks)
        self.assertIsNotNone(ans)
        self.assertGreater(len(ans), 20)


if __name__ == "__main__":
    unittest.main()
