"""
Unit tests for query intent router.
"""

import unittest
from src.retrieval.router import detect_modality_intent


class TestIntentRouter(unittest.TestCase):
    def test_visual_intent(self):
        self.assertEqual(detect_modality_intent("Show me the diagram of the engine"), "image-caption")
        self.assertEqual(detect_modality_intent("What does the Sky-Fortress schematic look like?"), "image-caption")
        self.assertEqual(detect_modality_intent("Display the map of Vaeloria"), "image-caption")

    def test_tabular_intent(self):
        self.assertEqual(detect_modality_intent("What are the artillery specifications and caliber table?"), "table")
        self.assertEqual(detect_modality_intent("Give me the stats and cost numbers for the siege engine"), "table")

    def test_text_intent(self):
        self.assertEqual(detect_modality_intent("What caused the formation of the Ashen Rift?"), "text")
        self.assertEqual(detect_modality_intent("Who is Captain Vane and why did he die?"), "text")


if __name__ == "__main__":
    unittest.main()
