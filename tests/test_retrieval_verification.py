"""
Unit Tests for Retrieval Entity Matching, Multi-Field Comparison, and Pre-Generation Verification.
"""

import unittest
from src.retrieval.entity_matcher import extract_entities, extract_requested_fields, analyze_query_structure
from src.retrieval.verifier import verify_and_filter_context, check_chunk_entity_match, check_chunk_field_match
from src.retrieval.retriever import retrieve
from src.generation.generator import generate_answer


class TestRetrievalVerification(unittest.TestCase):
    """
    Tests exact entity matching, field coverage, distractor rejection, and sufficiency verification.
    """

    def test_entity_extraction(self):
        """Tests precise extraction of single and multiple named entities."""
        # Single entity
        q1 = "What is the garrison strength of Marrowwatch?"
        e1 = extract_entities(q1)
        self.assertIn("Marrowwatch", e1)

        # Comparative entities
        q2 = "Compare the caliber of Vanguard Trebuchet and Cinder Mortar"
        e2 = extract_entities(q2)
        self.assertIn("Vanguard Trebuchet", e2)
        self.assertIn("Cinder Mortar", e2)

    def test_requested_fields_extraction(self):
        """Tests extracting all requested comparison fields."""
        q = "Compare the caliber, effective range, and cost of Dread Trebuchet and Vanguard Ballista"
        fields = extract_requested_fields(q)
        self.assertIn("caliber", fields)
        self.assertIn("range", fields)
        self.assertIn("cost", fields)

    def test_distractor_pruning_and_entity_matching(self):
        """Tests that chunks not containing the target entity are pruned."""
        query = "What is the recorded garrison strength of Marrowwatch?"
        chunks = [
            {
                "chunk_id": "c_correct",
                "document_name": "codex_vaeloria.pdf",
                "content": "Marrowwatch garrison is recorded as 3,107 soldiers under arms.",
                "raw_similarity": 0.8
            },
            {
                "chunk_id": "c_distractor",
                "document_name": "other_lore.pdf",
                "content": "The fortress of Oakhaven has high stone towers and iron gates.",
                "raw_similarity": 0.7
            }
        ]

        clean_chunks, report = verify_and_filter_context(query, chunks)
        self.assertEqual(len(clean_chunks), 1)
        self.assertEqual(clean_chunks[0]["chunk_id"], "c_correct")
        self.assertTrue(report["is_sufficient"])
        self.assertEqual(report["pruned_count"], 1)

    def test_rejection_of_unrelated_result_before_generation(self):
        """Tests that if all retrieved chunks fail entity verification, the generator rejects."""
        query = "What is the secret passphrase of the Shadow Citadel?"
        unrelated_chunks = [
            {
                "chunk_id": "c_unrelated_1",
                "document_name": "farm_records.pdf",
                "content": "The wheat harvest yielded forty bushels of grain.",
                "raw_similarity": 0.2
            }
        ]

        clean_chunks, report = verify_and_filter_context(query, unrelated_chunks)
        self.assertFalse(report["is_sufficient"])

        ans = generate_answer(query, unrelated_chunks)
        self.assertTrue(
            "outside the scope" in ans.lower() or "no documented information" in ans.lower(),
            f"Expected refusal message but got: {ans}"
        )

    def test_multi_field_coverage_reporting(self):
        """Tests that verifier tracks which requested fields are covered."""
        query = "What is the caliber and cost of the Vanguard Ballista?"
        chunks = [
            {
                "chunk_id": "c_ballista",
                "document_name": "specs.pdf",
                "content": "Vanguard Ballista has a 120mm caliber bore and costs 450 ducats.",
                "raw_similarity": 0.85
            }
        ]

        clean_chunks, report = verify_and_filter_context(query, chunks)
        self.assertTrue(report["field_coverage"]["caliber"]["found"])
        self.assertTrue(report["field_coverage"]["cost"]["found"])


if __name__ == "__main__":
    unittest.main()
