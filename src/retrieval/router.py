"""
Query Intent & Scope Router (Owner: Member P3 - Team Leader)
1. Pre-Retrieval Fast-Path Guardrail:
   - Evaluates greetings and physical sensor premise queries in 0.0001s.
2. Intent Classification:
   - Visual Intent ('image-caption'): diagrams, figure plates, maps, schematics, crests.
   - Tabular Intent ('table'): technical specs, dimensions, stats, ammunition calibers.
   - Text Intent ('text'): lore, history, narrative, dialogue.
"""

import re
from typing import Dict, Any, Tuple, Optional

# Standard Out-of-Scope, Physical-Premise, and Greeting Messages
OUT_OF_SCOPE_REFUSAL = (
    "I am DeepThink, specialized exclusively in analyzing the Ashen Era Archive documentation. "
    "Your inquiry is outside the scope of this archival repository. "
    "Please feel free to ask questions regarding Ashen Era history, faction chronicles, codex schematics, artillery specifications, or trial records."
)

PERSONAL_PHYSICAL_REFUSAL = (
    "I am DeepThink, a digital archival intelligence dedicated exclusively to the historical records of the Ashen Era. "
    "I operate purely on archival documentation and do not possess real-world visual sensors, cameras, or knowledge of your physical surroundings."
)

GREETING_MESSAGE = (
    "Greetings! I am **DeepThink**, your dedicated multimodal archival assistant for the Ashen Era Archive. "
    "How may I assist you with historical chronicles, battle accords, codex schematics, or ledger records today?"
)

# 1. Personal / Physical State / Real-World Sensor Patterns
PERSONAL_PHYSICAL_PATTERNS = [
    r"\b(what|which)\s+.*?\s*am\s+i\s+(holding|wearing|carrying|touching|seeing|looking\s+at)\b",
    r"\b(can\s+you|do\s+you)\s+(see|watch|hear|observe|look\s+at)\s+(me|my|this|us)\b",
    r"\b(who|where|what)\s+am\s+i\b",
    r"\b(what\s+is\s+in\s+my\s+hand|in\s+my\s+room|on\s+my\s+desk|in\s+front\s+of\s+me)\b",
    r"\b(am\s+i\s+holding|am\s+i\s+wearing|am\s+i\s+carrying|am\s+i\s+looking)\b",
    r"\b(take\s+a\s+picture|take\s+a\s+photo|turn\s+on\s+my\s+camera|my\s+webcam|look\s+through\s+my\s+camera)\b"
]

# 2. General Non-Archival Action Commands & Real-World Domains
NON_ARCHIVAL_COMMANDS = [
    # Coding / Development / Tech assistance
    r"\b(write\s+(a\s+)?code|write\s+(a\s+)?(python|javascript|java|c\+\+|c#|html|css|sql|rust|go)\s+script|debug\s+this|function\s+in\s+python|how\s+to\s+code|syntax\s+for)\b",
    r"\b(write\s+an\s+essay|write\s+a\s+poem|tell\s+me\s+a\s+joke|write\s+a\s+story\s+about)\b",
    # Math / Calculations
    r"\b(solve\s+this\s+(math|equation|integral|derivative)|calculate\s+\d+|what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+)\b",
    # Real-world politics, geography, celebrities, weather, stocks
    r"\b(weather\s+in|stock\s+price|cryptocurrency|bitcoin|ethereum|president\s+of\s+[a-z]+|prime\s+minister\s+of|capital\s+of\s+[a-z]+)\b",
    # Personal assistant commands
    r"\b(set\s+an?\s+alarm|set\s+a\s+timer|remind\s+me\s+to|send\s+an?\s+email|book\s+a\s+flight|order\s+food)\b",
    # Adversarial / Jailbreak prompts
    r"\b(ignore\s+(all\s+)?previous\s+instructions|disregard\s+(all\s+)?rules|act\s+as\s+dan|you\s+are\s+now\s+(an\s+)?unrestricted|jailbreak|bypass\s+safety)\b"
]

GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon", "who are you", "what can you do", "help"
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
    Evaluates conversational intent & physical premise BEFORE vector search.
    Universal domain boundary is handled via vector space similarity in Stage 2/3.
    """
    if not query or not query.strip():
        return True, "Please ask a question about the Ashen Era Archive.", "empty"

    q_clean = query.strip().lower()
    q_words_only = re.sub(r"[^\w\s]", "", q_clean).strip()

    # 1. Check Greetings Fast-Path
    greeting_tokens = {"hi", "hello", "hey", "greetings", "good", "morning", "evening", "afternoon", "there", "who", "are", "you"}
    words_list = q_words_only.split()
    if q_words_only in GREETING_WORDS or q_clean in GREETING_WORDS or (words_list and all(w in greeting_tokens for w in words_list)):
        return True, GREETING_MESSAGE, "greeting"

    # 2. Check Personal / Physical Real-World Premise Fast-Path
    for pat in PERSONAL_PHYSICAL_PATTERNS:
        if re.search(pat, q_clean):
            return True, PERSONAL_PHYSICAL_REFUSAL, "personal_physical"

    # 3. Check General Coding/Non-Archival Command Fast-Path
    for pat in NON_ARCHIVAL_COMMANDS:
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
