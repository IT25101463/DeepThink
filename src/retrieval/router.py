"""
Query Intent Router (Owner: Member P3 - Team Leader)
Analyzes user question to detect modality intent:
- Visual Intent ('image-caption'): diagrams, figure plates, maps, schematics, crests.
- Tabular Intent ('table'): technical specs, dimensions, stats, ammunition calibers.
- Text Intent ('text'): lore, history, narrative, dialogue.
"""

import re
from typing import Dict, Any, Tuple


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
        "Show me the diagram of the Sky-Fortress primary steam coolant valve",
        "What are the artillery specifications and caliber table for 155mm cannons?",
        "Who founded the Order of the Ashen Dawn and what was their charter?",
        "What does the map of Port Cinder look like?",
        "Compare the weight and effective range of the Dreadnought class vs Scout class"
    ]
    for q in test_queries:
        res = analyze_query_intent(q)
        print(f"Q: '{q}'\n  -> Intent: {res['intent']} | Target Modality: {res['target_modality']} | Boost: {res['boost_weight']}x\n")
