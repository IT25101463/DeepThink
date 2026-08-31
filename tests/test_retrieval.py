"""
Unit tests for Member P3 Retrieval Engine (Indexer, Router, Retriever).
"""

import unittest
from src.retrieval.router import analyze_query_intent, detect_modality_intent
from src.retrieval.retriever import retrieve
from src.retrieval.indexer import sanitize_metadata


class TestRetrievalEngine(unittest.TestCase):
    def test_intent_router_visual(self):
        res = analyze_query_intent("Show me the blueprint and diagram of the engine")
        self.assertEqual(res["target_modality"], "image-caption")
        self.assertEqual(res["intent"], "visual")
        self.assertGreater(res["boost_weight"], 1.0)

    def test_intent_router_tabular(self):
        res = analyze_query_intent("What are the artillery caliber specifications and rate of fire table?")
        self.assertEqual(res["target_modality"], "table")
        self.assertEqual(res["intent"], "tabular")
        self.assertGreater(res["boost_weight"], 1.0)

    def test_intent_router_narrative(self):
        res = analyze_query_intent("What happened to Captain Vane during the mutiny?")
        self.assertEqual(res["target_modality"], "text")
        self.assertEqual(res["intent"], "narrative_text")
        self.assertEqual(res["boost_weight"], 1.0)

    def test_metadata_sanitizer(self):
        raw_chunk = {
            "chunk_id": "test_01",
            "document_name": "Test.pdf",
            "page_number": 5,
            "modality": "image-caption",
            "media_path": "data/extracted_media/figures/test.png",
            "metadata": {"source_reliability": "official_codex", "word_count": 50}
        }
        meta = sanitize_metadata(raw_chunk)
        self.assertEqual(meta["chunk_id"], "test_01")
        self.assertEqual(meta["page_number"], 5)
        self.assertEqual(meta["source_reliability"], "official_codex")
        self.assertIsInstance(meta["page_number"], int)


if __name__ == "__main__":
    unittest.main()
