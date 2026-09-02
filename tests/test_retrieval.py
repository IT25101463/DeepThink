"""
Unit tests for Member P3 Retrieval Engine (Indexer, Router, Retriever, Universal OOD Evaluator).
"""

import unittest
from src.retrieval.router import analyze_query_intent, detect_modality_intent
from src.retrieval.retriever import retrieve, evaluate_retrieval_confidence
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

    def test_crag_confidence_evaluator_correct(self):
        chunks = [{
            "chunk_id": "c1",
            "document_name": "codex_vaeloria_i.pdf",
            "content": "Marrowwatch garrison recorded strength was 3,107 soldiers.",
            "raw_similarity": 0.85
        }]
        eval_res = evaluate_retrieval_confidence("What is the garrison strength of Marrowwatch?", chunks)
        self.assertEqual(eval_res["verdict"], "CORRECT")
        self.assertTrue(eval_res["is_in_domain"])
        self.assertGreaterEqual(eval_res["confidence_score"], 0.45)

    def test_universal_ood_evaluator_unlisted_domains(self):
        # Arbitrary unlisted domain: Quantum mechanics
        chunks_quantum = [{
            "chunk_id": "c2",
            "document_name": "unrelated_lore.pdf",
            "content": "The soldiers march across the stone bridges of the eastern valley.",
            "raw_similarity": 0.12
        }]
        eval_quantum = evaluate_retrieval_confidence("How does quantum superposition entanglement work?", chunks_quantum)
        self.assertEqual(eval_quantum["verdict"], "OUT_OF_DOMAIN")
        self.assertFalse(eval_quantum["is_in_domain"])

        # Arbitrary unlisted domain: Bitcoin cryptocurrency
        chunks_crypto = [{
            "chunk_id": "c3",
            "document_name": "lore.pdf",
            "content": "Gold coins and silver ducats were counted in the ledger.",
            "raw_similarity": 0.18
        }]
        eval_crypto = evaluate_retrieval_confidence("Explain Bitcoin blockchain proof of work mining", chunks_crypto)
        self.assertEqual(eval_crypto["verdict"], "OUT_OF_DOMAIN")
        self.assertFalse(eval_crypto["is_in_domain"])


if __name__ == "__main__":
    unittest.main()
