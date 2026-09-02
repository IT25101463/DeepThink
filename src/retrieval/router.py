"""
Query Intent & Scope Router (Owner: Member P3 - Team Leader)
1. Pre-Retrieval Domain Scope Guardrail:
   - Evaluates greetings and out-of-scope queries BEFORE touching vector database.
   - Fast-path refusal (0.001s latency, 0 vector DB calls, 0 token consumption).
2. Intent Classification:
   - Visual Intent ('image-caption'): diagrams, figure plates, maps, schematics, crests.
   - Tabular Intent ('table'): technical specs, dimensions, stats, ammunition calibers.
   - Text Intent ('text'): lore, history, narrative, dialogue.
"""

import re
from typing import Dict, Any, Tuple, Optional

# Standard Out-of-Scope and Greeting Messages
OUT_OF_SCOPE_REFUSAL = (
    "I am DeepThink, specialized exclusively in analyzing the Ashen Era Archive documentation. "
    "Your inquiry is outside the scope of this archival repository. "
    "Please feel free to ask questions regarding Ashen Era history, faction chronicles, codex schematics, artillery specifications, or trial records."
)

GREETING_MESSAGE = (
    "Greetings! I am **DeepThink**, your dedicated multimodal archival assistant for the Ashen Era Archive. "
    "How may I assist you with historical chronicles, battle accords, codex schematics, or ledger records today?"
)

OFF_DOMAIN_PATTERNS = [
    # Real-world geography & places
    r"\b(france|sri lanka|colombo|india|usa|america|london|paris|china|russia|japan|tokyo|germany|australia|canada|singapore|new york|california)\b",
    # Real-world people / celebrities / modern sports / pop culture
    r"\b(elon musk|donald trump|biden|obama|modi|messi|ronaldo|cricket|football|world cup|olympics|bollywood|hollywood|taylor swift)\b",
    # General coding / programming scripts
    r"\b(python|javascript|java|c\+\+|c#|write a code|write code|write a script|programming|html|css|sql|react|django|fastapi|debug this code|function in)\b",
    # Lifestyle / Cooking / Math trivia / General chitchat
    r"\b(recipe for|how to cook|bake a cake|how to make|lose weight|weather in|temperature in|solve this math|calculate \d+|tell me a joke|write a poem about love|write an essay)\b"
]

GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon", "who are you", "what can you do"
}

VISUAL_PATTERNS = [
    r"\b(diagram|diagrams|schematic|schematics|blueprint|blueprints)\b",
    r"\b(figure|figures|figure plate|plate|plates)\b",
    r"\b(map|maps|cartography|chart|charts)\b",
    r"\b(drawing|drawings|sketch|sketches|illustration|illustrations)\b",
    r"\b(look like|looks like|appearance|depicted|depiction)\b",
    r"\b(image|images|picture|pictures|photo|visual|visualize)\b",
    r"\b(crest|emblem|insignia|seal|coat of arms)\b",
    r"\b(cross-section|layout|assembly|anatomy)\b",
    r"\b(show me|display|view)\b"
]

TABULAR_PATTERNS = [
    r"\b(table|tables|matrix|matrices|ledger|ledgers)\b",
    r"\b(spec|specs|specification|specifications)\b",
    r"\b(stat|stats|statistics|metrics)\b",
    r"\b(caliber|calibers|rate of fire|rpm|effective range|muzzle velocity)\b",
    r"\b(cost|costs|price|prices|allowance|budget)\b",
    r"\b(dimensions|weight|height|width|payload|capacity|tonnage)\b",
    r"\b(comparison|compare|breakdown|sheet|datasheet)\b"
]


def check_query_domain_scope(query: str) -> Tuple[bool, Optional[str], str]:
    """
    Evaluates domain scope BEFORE vector search.
    Returns: (is_handled, response_text, category)
      - If handled: category is 'greeting' or 'out_of_scope'
      - If in-scope: (False, None, 'in_scope')
    """
    if not query or not query.strip():
        return True, "Please ask a question about the Ashen Era Archive.", "empty"

    q_clean = query.strip().lower()
    q_words_only = re.sub(r"[^\w\s]", "", q_clean).strip()

    # 1. Check Greetings Fast-Path
    if q_words_only in GREETING_WORDS or q_clean in GREETING_WORDS:
        return True, GREETING_MESSAGE, "greeting"

    # 2. Check Explicit Off-Domain Patterns Fast-Path
    for pat in OFF_DOMAIN_PATTERNS:
        if re.search(pat, q_clean):
            return True, OUT_OF_SCOPE_REFUSAL, "out_of_scope"

    return False, None, "in_scope"


def analyze_query_intent(query: str) -> Dict[str, Any]:
    """
    Performs rich intent classification and returns intent metadata,
    target modality, and modality boost multipliers.
    """
    q_lower = query.lower().strip()
    
    # Check visual pattern matches
    visual_matches = [p for p in VISUAL_PATTERNS if re.search(p, q_lower)]
    visual_score = len(visual_matches)
    
    # Check tabular pattern matches
    tabular_matches = [p for p in TABULAR_PATTERNS if re.search(p, q_lower)]
    tabular_score = len(tabular_matches)
    
    if visual_score > 0 and visual_score >= tabular_score:
        return {
            "intent": "visual",
            "target_modality": "image-caption",
            "boost_weight": 1.6,
            "matched_terms": visual_matches
        }
    elif tabular_score > 0:
        return {
            "intent": "tabular",
            "target_modality": "table",
            "boost_weight": 1.4,
            "matched_terms": tabular_matches
        }
    else:
        return {
            "intent": "narrative_text",
            "target_modality": "text",
            "boost_weight": 1.0,
            "matched_terms": []
        }


def detect_modality_intent(query: str) -> str:
    """
    Convenience wrapper returning the target modality string: 'image-caption', 'table', or 'text'.
    """
    return analyze_query_intent(query)["target_modality"]


if __name__ == "__main__":
    test_queries = [
        "What is the capital of France?",
        "Hi, good morning!",
        "Show me the diagram of the Sky-Fortress primary steam coolant valve",
        "What are the artillery specifications and caliber table for 155mm cannons?",
        "Who founded the Order of the Ashen Dawn?"
    ]
    for q in test_queries:
        handled, msg, cat = check_query_domain_scope(q)
        if handled:
            print(f"FAST-PATH Refusal/Greeting [{cat}]: '{q}'\n -> {msg[:60]}...\n")
        else:
            intent = analyze_query_intent(q)
            print(f"IN-SCOPE Retrieval [{intent['intent']}]: '{q}'\n")
