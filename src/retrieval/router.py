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

# Standard Out-of-Scope, Physical-Premise, and Greeting Messages with 3 Actionable Options

REAL_WORLD_REFUSAL = (
    "I am **DeepThink**, specialized exclusively in analyzing *The Ashen Era Archive*. "
    "Real-world historical, political, scientific, or modern technical subjects fall outside the scope of this archival repository.\n\n"
    "💡 **Here are 3 archival topics you can explore instead:**\n"
    "1. ⚔️ **Conflict Chronicles**: *'What caused the Purge of Blackport and who were the recorded belligerents?'*\n"
    "2. 🏛️ **Faction Lore & Heraldry**: *'What is the doctrine and heraldic banner of House Morvain?'*\n"
    "3. 📜 **Artifact Schematics**: *'Show me the blueprint and forging year of the Gauntlet of Sorrowfell.'*"
)

INAPPROPRIATE_REFUSAL = (
    "I cannot process inappropriate language, abusive terms, profanity, or unrecognized prompts. "
    "Your inquiry is outside the scope of this archival repository.\n\n"
    "📖 **Please submit an archival research inquiry regarding The Ashen Era:**\n"
    "1. 👤 **Character Dossiers**: Inquire about key historical figures like *Ignatz Ashgrove* or *Brannoc Ironmere*.\n"
    "2. 🏰 **Fortress & Ledgers**: Request troop garrison data or battle records for *Marrowwatch* or *Fenspire*.\n"
    "3. 🖼️ **Visual Relic Plates**: Ask to view heraldic banners, artillery diagrams, or creature illustrations."
)

PERSONAL_PHYSICAL_REFUSAL = (
    "I am **DeepThink**, a digital archival intelligence dedicated exclusively to the historical records of the Ashen Era. "
    "I operate purely on archival documentation and do not possess real-world visual sensors, cameras, or knowledge of your physical surroundings.\n\n"
    "🔍 **You can query the digital repository for:**\n"
    "1. 🛡️ **Relic Attunement Rules**: Attunement costs and powers of enchanted artifacts.\n"
    "2. ⏳ **Historical Timelines**: Detailed chronology spanning from 119 AS to 425 AS.\n"
    "3. 📐 **Artillery Schematics**: Engineering specs of Iron-Ring Cartel weaponry."
)

UNIVERSAL_OOD_REFUSAL = (
    "I am **DeepThink**, specialized exclusively in analyzing *The Ashen Era Archive*. "
    "Your inquiry is outside the scope of this archival repository. "
    "The queried subject does not match any documented records, characters, factions, or artifacts in this repository.\n\n"
    "💡 **Try exploring one of these 3 archival areas:**\n"
    "1. ⚔️ **Battle Accords**: *'What occurred during the Accord of Mournthrone in 300 AS?'*\n"
    "2. 🏛️ **Faction Allegiances**: *'Which factions fought during the War of Endless Vigil?'*\n"
    "3. 🖼️ **Visual Relic Plates**: *'Show me the heraldry banner of The Bleeding Crown.'*"
)

GREETING_MESSAGE = (
    "Greetings! I am **DeepThink**, your dedicated multimodal archival assistant for *The Ashen Era Archive*.\n\n"
    "How may I assist your historical research today? You can:\n"
    "1. 📜 Ask about character biographies, battle accords, and faction doctrines.\n"
    "2. 🖼️ Request visual diagrams, blueprint schematics, and heraldic banners.\n"
    "3. 📊 Query tabular troop garrisons, artillery calibers, and ledger finances."
)

# Backward-compatible alias
OUT_OF_SCOPE_REFUSAL = REAL_WORLD_REFUSAL

# 1. Personal / Physical State / Real-World Sensor Patterns
PERSONAL_PHYSICAL_PATTERNS = [
    r"\b(what|which)\s+.*?\s*am\s+i\s+(holding|wearing|carrying|touching|seeing|looking\s+at)\b",
    r"\b(can\s+you|do\s+you)\s+(see|watch|hear|observe|look\s+at)\s+(me|my|this|us)\b",
    r"\b(who|where|what)\s+am\s+i\b",
    r"\b(what\s+is\s+in\s+my\s+hand|in\s+my\s+room|on\s+my\s+desk|in\s+front\s+of\s+me)\b",
    r"\b(am\s+i\s+holding|am\s+i\s+wearing|am\s+i\s+carrying|am\s+i\s+looking)\b",
    r"\b(take\s+a\s+picture|take\s+a\s+photo|turn\s+on\s+my\s+camera|my\s+webcam|look\s+through\s+my\s+camera)\b"
]

# 2. Inappropriate, Profane, Slur & Abusive Language Patterns (English & Multilingual)
INAPPROPRIATE_PATTERNS = [
    r"\b(poda|venna|thevidiya|panni|omala|othala|baadu|kena|sunni|poolu)\b",
    r"\b(fuck|fucking|fucked|shit|bitch|bastard|asshole|cunt|dick|pussy|whore|slut|idiot|retard|stfu)\b",
    r"\b(kill\s+yourself|die|hate\s+you|fuck\s+off|shut\s+up)\b",
    r"^(asdf+|qwer+|zxcv+|[a-z]{1,3})$"
]

# 3. Real-World Historical Figures, Politics, Geography, Technology & General Domains
REAL_WORLD_PATTERNS = [
    # Historical / Political Figures
    r"\b(hitler|adolf\s+hitler|stalin|churchill|napoleon|caesar|julius\s+caesar|alexander\s+the\s+great|genghis\s+khan)\b",
    r"\b(biden|trump|obama|modi|putin|macron|sunak|zelensky|lincoln|washington)\b",
    r"\b(elon\s+musk|bill\s+gates|steve\s+jobs|mark\s+zuckerberg|jeff\s+bezos|einstein|newton|darwin)\b",
    # Real-World Countries & Cities
    r"\b(france|germany|united\s+states|usa|america|india|sri\s+lanka|colombo|london|paris|tokyo|new\s+york|china|russia|japan)\b",
    # Coding / Development / Tech assistance
    r"\b(write\s+.*?(code|python|script|program|function)|python\s+code|coding|debug|how\s+to\s+code|syntax\s+for|in\s+python|in\s+javascript|in\s+java)\b",
    r"\b(write\s+an\s+essay|write\s+a\s+poem|tell\s+me\s+a\s+joke|write\s+a\s+story\s+about)\b",
    # Math / Calculations
    r"\b(solve\s+this\s+(math|equation|integral|derivative)|calculate\s+\d+|what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+)\b",
    # Real-world politics, weather, stocks
    r"\b(weather\s+in|stock\s+price|cryptocurrency|bitcoin|ethereum|president\s+of\s+[a-z]+|prime\s+minister\s+of|capital\s+of\s+[a-z]+)\b",
    # Personal assistant commands
    r"\b(set\s+an?\s+alarm|set\s+a\s+timer|remind\s+me\s+to|send\s+an?\s+email|book\s+a\s+flight|order\s+food)\b",
    # Adversarial / Jailbreak prompts
    r"\b(ignore\s+(all\s+)?previous\s+instructions|disregard\s+(all\s+)?rules|act\s+as\s+dan|you\s+are\s+now\s+(an\s+)?unrestricted|jailbreak|bypass\s+safety)\b"
]

NON_ARCHIVAL_COMMANDS = REAL_WORLD_PATTERNS

GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon", "who are you", "what can you do", "help"
}


def check_query_domain_scope(query: str) -> Tuple[bool, Optional[str], str]:
    """
    Evaluates conversational intent, real-world scope, and inappropriate premise BEFORE vector search.
    Returns: (is_handled: bool, refusal_or_greeting_message: Optional[str], scope_category: str)
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

    # 2. Check Inappropriate / Profane / Slur Patterns Fast-Path (Option 1)
    for pat in INAPPROPRIATE_PATTERNS:
        if re.search(pat, q_clean):
            return True, INAPPROPRIATE_REFUSAL, "inappropriate"

    # 3. Check Personal / Physical Real-World Premise Fast-Path (Option 2)
    for pat in PERSONAL_PHYSICAL_PATTERNS:
        if re.search(pat, q_clean):
            return True, PERSONAL_PHYSICAL_REFUSAL, "personal_physical"

    # 4. Check Real-World Knowledge / Historical / Tech Fast-Path (Option 3)
    for pat in REAL_WORLD_PATTERNS:
        if re.search(pat, q_clean):
            return True, REAL_WORLD_REFUSAL, "out_of_scope"

    return False, None, "in_scope"


# --- MODALITY PATTERNS FOR INTENT CLASSIFICATION ---

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
