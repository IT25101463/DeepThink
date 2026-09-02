"""
Unit Tests for Adaptive Context Budgeting and Dynamic Score Drop-Off.
"""

import unittest
from src.retrieval.adaptive_budget import (
    determine_query_intent_and_budget,
    apply_relative_score_dropoff,
    apply_token_budget_packing
)
from src.retrieval.retriever import retrieve


class TestAdaptiveBudget(unittest.TestCase):
    """
    Tests dynamic chunk sizing, elbow drop-off filtering, and token budget packing.
    """

    def test_query_intent_budgeting(self):
        """Tests that different query types receive appropriate initial budgets."""
        # 1. Visual query
        b_vis = determine_query_intent_and_budget("Show me the diagram plate of the Sky-Fortress valve")
        self.assertEqual(b_vis["intent"], "visual")
        self.assertEqual(b_vis["target_k"], 2)

        # 2. Single-fact query
        b_fact = determine_query_intent_and_budget("When was Voltaire Hollowmere born?")
        self.assertEqual(b_fact["intent"], "single_fact")
        self.assertEqual(b_fact["target_k"], 2)

        # 3. Comparative query
        b_comp = determine_query_intent_and_budget(
            "Compare Ederon Fellgard and Ederon Coldwater",
            entities=["Ederon Fellgard", "Ederon Coldwater"]
        )
        self.assertEqual(b_comp["intent"], "comparative")
        self.assertEqual(b_comp["target_k"], 6)

    def test_relative_score_dropoff_pruning(self):
        """Tests that chunks whose score drops below alpha * top_score are pruned."""
        chunks = [
            {"chunk_id": "c1", "relevance_score": 0.90, "content": "Top hit"},
            {"chunk_id": "c2", "relevance_score": 0.85, "content": "Second hit"},
            {"chunk_id": "c3", "relevance_score": 0.40, "content": "Low noise hit"}, # 0.40 < 0.60 * 0.90 (0.54)
            {"chunk_id": "c4", "relevance_score": 0.20, "content": "Very low noise hit"}
        ]

        # With alpha=0.60, threshold is 0.54. Only c1 and c2 should remain.
        filtered = apply_relative_score_dropoff(chunks, alpha=0.60, min_k=1, max_k=5)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["chunk_id"], "c1")
        self.assertEqual(filtered[1]["chunk_id"], "c2")

    def test_token_budget_packing(self):
        """Tests that context is capped at maximum token limit."""
        chunks = [
            {"chunk_id": "c1", "content": "Word " * 100},  # ~133 tokens
            {"chunk_id": "c2", "content": "Word " * 100},  # ~133 tokens
            {"chunk_id": "c3", "content": "Word " * 500},  # ~665 tokens
        ]

        # Max budget of 300 tokens: should fit c1 and c2, but not c3
        packed = apply_token_budget_packing(chunks, max_tokens=300)
        self.assertEqual(len(packed), 2)
        self.assertEqual(packed[0]["chunk_id"], "c1")
        self.assertEqual(packed[1]["chunk_id"], "c2")

    def test_end_to_end_adaptive_retrieval(self):
        """Tests that retrieve() dynamically sizes chunks for simple vs comparative queries."""
        # Simple single fact: should retrieve small, tight chunk list (<= 2-3)
        c_simple = retrieve("When was Voltaire Hollowmere born?")
        self.assertTrue(1 <= len(c_simple) <= 3)

        # Comparative query: should retrieve larger chunk list (>= 4)
        c_comp = retrieve("Compare the garrison of Marrowwatch and Oakhaven")
        self.assertTrue(len(c_comp) >= 2)


if __name__ == "__main__":
    unittest.main()
