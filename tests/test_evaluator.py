"""
Unit tests for Member P4 Automated Benchmark Evaluator.
"""

import unittest
from pathlib import Path

from src.evaluation.evaluator import (
    evaluate_retrieval_precision,
    evaluate_citation_accuracy,
    evaluate_hallucination,
    evaluate_modality_success,
    run_benchmark
)


class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.sample_chunks = [
            {
                "chunk_id": "test_chunk_01",
                "document_name": "the_ashen_chronicles_vol_i.pdf",
                "page_number": 3,
                "modality": "text",
                "content": "Ignatz Ashgrove carried the Broken Scepter during the exile.",
                "media_path": None,
                "caption": None
            },
            {
                "chunk_id": "test_chunk_02",
                "document_name": "plate_08_creature_weeping_lurker.png",
                "page_number": 1,
                "modality": "image-caption",
                "content": "Official threat rating: Class 4. Creature: Weeping Lurker.",
                "media_path": "data/extracted_media/figures/plate_08_creature_weeping_lurker.png",
                "caption": "Weeping Lurker Threat Classification"
            }
        ]

    def test_evaluate_retrieval_precision_text(self):
        passed = evaluate_retrieval_precision("What was Ignatz Ashgrove holding?", self.sample_chunks, "text")
        self.assertTrue(passed)

    def test_evaluate_retrieval_precision_visual(self):
        passed = evaluate_retrieval_precision("Show the Weeping Lurker threat rating", self.sample_chunks, "image-caption")
        self.assertTrue(passed)

    def test_evaluate_citation_accuracy_valid(self):
        answer = "Ignatz carried the scepter according to [the_ashen_chronicles_vol_i.pdf, Page 3]."
        valid = evaluate_citation_accuracy(answer, self.sample_chunks)
        self.assertTrue(valid)

    def test_evaluate_citation_accuracy_missing(self):
        answer = "Ignatz carried the scepter without any source."
        valid = evaluate_citation_accuracy(answer, self.sample_chunks)
        self.assertFalse(valid)

    def test_evaluate_hallucination(self):
        grounded = "The archive records do not specify the exact weight."
        self.assertFalse(evaluate_hallucination(grounded, []))

    def test_evaluate_modality_success(self):
        ans_with_img = "Here is the figure: ![Weeping Lurker](data/extracted_media/figures/plate_08_creature_weeping_lurker.png)"
        success = evaluate_modality_success("Show Lurker", ans_with_img, self.sample_chunks, "image-caption")
        self.assertTrue(success)

    def test_benchmark_runner_subset(self):
        res = run_benchmark(limit=2, update_metrics_doc=False, output_json=None)
        self.assertIn("total_questions", res)
        self.assertEqual(res["total_questions"], 2)


if __name__ == "__main__":
    unittest.main()
