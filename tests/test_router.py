"""
Unit tests for query intent router and pre-retrieval domain guardrails.
"""

import unittest
from src.retrieval.router import (
    detect_modality_intent, 
    check_query_domain_scope, 
    analyze_query_intent
)


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

    def test_personal_physical_guardrail(self):
        handled, msg, cat = check_query_domain_scope("what emblem am I holding")
        self.assertTrue(handled)
        self.assertEqual(cat, "personal_physical")
        self.assertIn("visual sensors", msg.lower())

        handled2, msg2, cat2 = check_query_domain_scope("Can you see what is on my desk?")
        self.assertTrue(handled2)
        self.assertEqual(cat2, "personal_physical")

    def test_non_archival_command_guardrail(self):
        handled, msg, cat = check_query_domain_scope("Write a python script for sorting an array")
        self.assertTrue(handled)
        self.assertEqual(cat, "out_of_scope")

    def test_greetings_fast_path(self):
        handled, msg, cat = check_query_domain_scope("Hi, good morning!")
        self.assertTrue(handled)
        self.assertEqual(cat, "greeting")

    def test_farewell_fast_path(self):
        for farewell in ("bye", "Goodbye!", "see you"):
            handled, msg, cat = check_query_domain_scope(farewell)
            self.assertTrue(handled)
            self.assertEqual(cat, "farewell")
            self.assertIn("Goodbye", msg)

    def test_in_scope_pass_through(self):
        handled, msg, cat = check_query_domain_scope("Who founded the Order of the Ashen Vanguard?")
        self.assertFalse(handled)
        self.assertIsNone(msg)
        self.assertEqual(cat, "in_scope")


if __name__ == "__main__":
    unittest.main()
