"""
Comprehensive Unit Tests for RAG 3.0 (Agentic, Multi-Hop, Re-Ranking, and Table Aggregation).
"""

import unittest
from src.retrieval.agentic import is_complex_query, decompose_query, agentic_retrieve
from src.retrieval.reranker import rerank_chunks, compute_cross_relevance
from src.retrieval.table_aggregator import parse_markdown_table, aggregate_numeric_column, extract_and_aggregate_tables
from src.retrieval.retriever import retrieve
from src.generation.generator import generate_answer, synthesize_grounded_fallback


class TestRAG3CompoundSystem(unittest.TestCase):
    """
    Test suite for RAG 3.0 advanced capabilities.
    """

    def test_query_complexity_detection(self):
        """Tests classification of complex vs simple queries."""
        # Comparative
        is_comp, q_type = is_complex_query("Compare the garrison of Marrowwatch with Oakhaven")
        self.assertTrue(is_comp)
        self.assertEqual(q_type, "comparative")

        # Multi-Hop
        is_comp, q_type = is_complex_query("Who was the mentor of the commander who signed the treaty?")
        self.assertTrue(is_comp)
        self.assertEqual(q_type, "multi_hop")

        # Quantitative
        is_comp, q_type = is_complex_query("What is the total expenditure and cost of all artillery?")
        self.assertTrue(is_comp)
        self.assertEqual(q_type, "quantitative")

        # Global Summary
        is_comp, q_type = is_complex_query("Provide an overview of all battles across the Ashen Era")
        self.assertTrue(is_comp)
        self.assertEqual(q_type, "global_summary")

        # Simple factual
        is_comp, q_type = is_complex_query("When was the Accord of Mournthrone signed?")
        self.assertFalse(is_comp)
        self.assertEqual(q_type, "simple")

    def test_query_decomposition(self):
        """Tests decomposition of comparative queries into atomic sub-queries."""
        sub_qs = decompose_query("Compare the garrison of Marrowwatch and Oakhaven")
        self.assertGreaterEqual(len(sub_qs), 2)
        self.assertTrue(any("marrowwatch" in sq.lower() for sq in sub_qs))
        self.assertTrue(any("oakhaven" in sq.lower() for sq in sub_qs))

    def test_agentic_multi_hop_retrieval_fusion(self):
        """Tests fusing sub-query lookups in agentic_retrieve."""
        # Mock base retriever function
        def mock_base_retriever(q: str, top_k: int = 5):
            if "marrowwatch" in q.lower():
                return [{
                    "chunk_id": "c_marrow",
                    "document_name": "codex_marrow.pdf",
                    "content": "Marrowwatch garrison strength: 3,107 troops.",
                    "relevance_score": 0.8
                }]
            elif "oakhaven" in q.lower():
                return [{
                    "chunk_id": "c_oakhaven",
                    "document_name": "codex_oakhaven.pdf",
                    "content": "Oakhaven garrison strength: 1,850 troops.",
                    "relevance_score": 0.75
                }]
            return []

        fused = agentic_retrieve("Compare Marrowwatch and Oakhaven", mock_base_retriever, top_k=5)
        self.assertEqual(len(fused), 2)
        doc_names = [c["document_name"] for c in fused]
        self.assertIn("codex_marrow.pdf", doc_names)
        self.assertIn("codex_oakhaven.pdf", doc_names)

    def test_reranker_prioritization(self):
        """Tests that cross-relevance scoring prioritizes exact multi-entity coverage."""
        query = "Vanguard Trebuchet brimstone caliber"
        chunks = [
            {
                "chunk_id": "c_weak",
                "document_name": "misc.pdf",
                "content": "The soldiers loaded the catapult with regular stones.",
                "relevance_score": 0.6,
                "raw_similarity": 0.5
            },
            {
                "chunk_id": "c_strong",
                "document_name": "artillery_codex.pdf",
                "content": "The Vanguard Trebuchet fires 450 cubit brimstone caliber shells.",
                "relevance_score": 0.55,
                "raw_similarity": 0.5
            }
        ]

        reranked = rerank_chunks(query, chunks, top_k=2)
        self.assertEqual(reranked[0]["chunk_id"], "c_strong")
        self.assertGreater(reranked[0]["rerank_score"], reranked[1]["rerank_score"])

    def test_table_parsing_and_aggregation(self):
        """Tests parsing markdown tables and computing column aggregates."""
        sample_table = (
            "| Weapon Name | Caliber (mm) | Cost (Ducats) |\n"
            "| :--- | :--- | :--- |\n"
            "| Vanguard Ballista | 120 | 450 |\n"
            "| Cinder Mortar | 240 | 850 |\n"
            "| Dread Trebuchet | 300 | 1200 |"
        )

        rows = parse_markdown_table(sample_table)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["Weapon Name"], "Vanguard Ballista")

        agg_cost = aggregate_numeric_column(rows, "Cost (Ducats)")
        self.assertEqual(agg_cost["count"], 3)
        self.assertEqual(agg_cost["sum"], 2500.0)
        self.assertEqual(agg_cost["min"], 450.0)
        self.assertEqual(agg_cost["max"], 1200.0)

    def test_extract_and_aggregate_tables_integration(self):
        """Tests end-to-end table analysis with chunks."""
        chunks = [{
            "chunk_id": "tbl_01",
            "document_name": "quartermaster_ledger.pdf",
            "page_number": 5,
            "modality": "table",
            "content": (
                "| Unit | Soldiers | Cost |\n"
                "|---|---|---|\n"
                "| Regiment Alpha | 500 | 1000 |\n"
                "| Regiment Beta | 300 | 600 |"
            )
        }]

        res = extract_and_aggregate_tables("What is the total cost across units?", chunks)
        self.assertTrue(res["has_tables"])
        self.assertIn("Cost", res["aggregates"])
        self.assertEqual(res["aggregates"]["Cost"]["sum"], 1600.0)

    def test_generator_with_table_aggregates(self):
        """Tests that generator includes quantitative table analysis."""
        chunks = [{
            "chunk_id": "tbl_02",
            "document_name": "quartermaster_ledger.pdf",
            "page_number": 5,
            "modality": "table",
            "content": (
                "| Unit | Cost |\n"
                "|---|---|\n"
                "| Alpha | 1000 |\n"
                "| Beta | 600 |"
            ),
            "raw_similarity": 0.85
        }]

        ans = generate_answer("What is the total cost of all units?", chunks)
        normalized_answer = ans.replace(",", "")
        self.assertIn("1600", normalized_answer)


if __name__ == "__main__":
    unittest.main()
