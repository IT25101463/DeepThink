"""
Unit tests for Member P4 Streamlit Web Application helpers.
"""

import unittest
from pathlib import Path
from src.ui.app import load_sample_questions, get_corpus_stats


class TestUI(unittest.TestCase):
    def test_load_sample_questions(self):
        questions = load_sample_questions()
        self.assertIsInstance(questions, list)
        if questions:
            self.assertIn("qid", questions[0])
            self.assertIn("question", questions[0])

    def test_get_corpus_stats(self):
        stats = get_corpus_stats()
        self.assertIn("total_chunks", stats)
        self.assertIn("figures_count", stats)
        self.assertIn("tables_count", stats)
        self.assertIn("is_indexed", stats)
        self.assertGreaterEqual(stats["total_chunks"], 0)


if __name__ == "__main__":
    unittest.main()
