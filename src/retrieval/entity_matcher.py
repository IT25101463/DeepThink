"""
Entity & Field Extraction Engine
Extracts target proper nouns/entities, requested attribute fields, and comparative pairs
from user queries to guarantee exact entity matching and multi-field coverage.
"""

import re
from typing import List, Dict, Any, Set, Tuple

# Common archival attribute fields that users ask to inspect or compare
KNOWN_FIELDS = {
    "faction": ["faction", "factions", "allegiance", "allegiances", "house", "cartel", "order", "alliance", "membership", "affiliations", "affiliation"],
    "role": ["role", "roles", "occupation", "profession", "duty", "duties", "sapper", "title", "position", "rank"],
    "birth_year": ["birth year", "birth years", "born", "birth", "birthdate", "age"],
    "service_location": ["service location", "service locations", "service station", "station", "place of service", "served at", "posting"],
    "caliber": ["caliber", "calibers", "bore", "bore size", "ammunition"],
    "range": ["range", "effective range", "maximum range", "distance"],
    "cost": ["cost", "price", "budget", "ducats", "expenditure", "allowance", "value"],
    "rate_of_fire": ["rate of fire", "rpm", "firing rate", "reload time", "shots per minute"],
    "garrison": ["garrison", "garrison strength", "troop count", "soldiers", "souls under arms", "troops", "personnel", "complement"],
    "dimensions": ["dimensions", "weight", "height", "width", "length", "tonnage", "mass", "payload"],
    "date": ["date", "year", "when", "time", "signed", "ratified", "founded", "occurred", "fell"],
    "signatory": ["signatory", "signatories", "signed by", "parties", "who signed", "commanders", "leaders"],
    "commander": ["commander", "leader", "captain", "general", "high commander", "officer", "mentor", "successor"],
    "location": ["location", "region", "where", "site", "fortress", "city", "realm", "territory", "province"],
    "composition": ["material", "materials", "construction", "made of", "metal", "brimstone", "alloy"],
    "diagram": ["diagram", "schematic", "blueprint", "figure plate", "plate", "drawing", "illustration", "map"]
}

STOP_WORDS = {
    "what", "which", "where", "when", "who", "whom", "whose", "why", "how",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "the", "a", "an", "and", "or", "but", "if", "then",
    "so", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "than", "too", "very", "can", "will", "just", "should", "now",
    "show", "tell", "give", "display", "find", "explain", "describe", "me", "you",
    "please", "compare", "comparison", "difference", "versus", "between", "according",
    "official", "record", "records", "archive", "ashen", "era", "document", "documentation"
}


def extract_requested_fields(query: str) -> List[str]:
    """
    Extracts canonical field names requested in the query (e.g. ['caliber', 'range', 'cost']).
    """
    q_lower = query.lower()
    matched_fields = []
    
    for canonical_name, aliases in KNOWN_FIELDS.items():
        for alias in aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, q_lower):
                if canonical_name not in matched_fields:
                    matched_fields.append(canonical_name)
                break
                
    return matched_fields


def extract_entities(query: str) -> List[str]:
    """
    Extracts specific target subjects / entities from the query.
    Prioritizes capitalized proper nouns, quoted phrases, and clean comparative pairs.
    """
    entities = []
    q_clean = query.strip()

    # Domain meta words to exclude from being treated as primary entities
    corpus_stopwords = {"ashen era", "ashen", "era", "archive", "archive records", "records", "codex", "annals"}

    # 1. Quoted terms (e.g. "Dread Trebuchet")
    quoted = re.findall(r'["\'](.*?)["\']', q_clean)
    for q in quoted:
        q_strip = q.strip()
        if len(q_strip) >= 3 and q_strip.lower() not in STOP_WORDS and q_strip.lower() not in corpus_stopwords:
            entities.append(q_strip)

    # 2. Extract Title Cased proper nouns or capitalized phrases (e.g. "Dread Trebuchet", "Marrowwatch", "Obsidian Dragon")
    cap_phrases = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]*(?:\s+[A-Z][a-zA-Z0-9_\-]*)*\b", q_clean)
    for phrase in cap_phrases:
        p_clean = _clean_entity_phrase(phrase)
        if (p_clean and 
            p_clean.lower() not in STOP_WORDS and 
            p_clean.lower() not in corpus_stopwords and 
            len(p_clean) >= 3):
            # Check it is not purely an attribute name
            field_words = {w for aliases in KNOWN_FIELDS.values() for a in aliases for w in a.split()}
            if not all(w.lower() in field_words or w.lower() in STOP_WORDS for w in p_clean.split()):
                if not any(p_clean.lower() == e.lower() for e in entities):
                    entities.append(p_clean)

    # If capitalized entities were successfully identified, return them directly
    if entities:
        return entities

    # 3. If no capitalized entity was found, inspect comparative patterns
    comp_match = re.search(r"(?:compare|difference between)\s+(.+?)\s+(?:and|with|to)\s+(.+?)(?:\?|$)", q_clean, re.IGNORECASE)
    vs_match = re.search(r"(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\?|$)", q_clean, re.IGNORECASE)

    if comp_match:
        part1 = comp_match.group(1).strip()
        part2 = comp_match.group(2).strip()
        e1 = _clean_entity_phrase(part1)
        e2 = _clean_entity_phrase(part2)
        if e1 and e1.lower() not in STOP_WORDS and e1.lower() not in corpus_stopwords:
            entities.append(e1)
        if e2 and e2.lower() not in STOP_WORDS and e2.lower() not in corpus_stopwords:
            entities.append(e2)
    elif vs_match:
        e1 = _clean_entity_phrase(vs_match.group(1).strip())
        e2 = _clean_entity_phrase(vs_match.group(2).strip())
        if e1 and e1.lower() not in STOP_WORDS and e1.lower() not in corpus_stopwords:
            entities.append(e1)
        if e2 and e2.lower() not in STOP_WORDS and e2.lower() not in corpus_stopwords:
            entities.append(e2)

    # 4. Fallback: non-stopword compound tokens
    if not entities:
        tokens = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", q_clean) if w.lower() not in STOP_WORDS and w.lower() not in corpus_stopwords]
        field_words = {w for aliases in KNOWN_FIELDS.values() for a in aliases for w in a.split()}
        filtered_tokens = [w for w in tokens if w.lower() not in field_words]
        if filtered_tokens:
            entities.append(" ".join(filtered_tokens))

    # Deduplicate while preserving case
    deduped = []
    seen = set()
    for e in entities:
        if e.lower() not in seen:
            seen.add(e.lower())
            deduped.append(e)

    return deduped


def _clean_entity_phrase(phrase: str) -> str:
    """
    Strips leading articles, requested field names, and prepositions from an entity phrase.
    e.g. 'the caliber, range, and garrison of Marrowwatch' -> 'Marrowwatch'
    """
    cleaned = phrase.strip().strip(",.?!\"'")
    
    # Strip leading "the", "a", "an", "all", "both", "are", "is", "were", "was", "compare"
    cleaned = re.sub(r"^(the|a|an|both|all|each|are|is|were|was|did|do|does|can|could|will|would|compare)\s+", "", cleaned, flags=re.IGNORECASE).strip()

    # Strip field prefixes like "caliber and range of", "specifications for", "garrison of"
    field_alias_pattern = r"^(?:the\s+)?(?:" + "|".join([re.escape(a) for aliases in KNOWN_FIELDS.values() for a in aliases]) + r"|\band\b|\bor\b|\bof\b|\bfor\b|\bbetween\b|\bin\b|\s|,)+\s+(?:of|for|in|at)\s+"
    cleaned = re.sub(field_alias_pattern, "", cleaned, flags=re.IGNORECASE).strip()

    # Final cleanup of leading prepositions
    cleaned = re.sub(r"^(?:of|for|in|at|on|with|regarding|about)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def analyze_query_structure(query: str) -> Dict[str, Any]:
    """
    Comprehensive query analysis returning target entities, requested fields,
    and whether the query is comparative or multi-attribute.
    """
    entities = extract_entities(query)
    fields = extract_requested_fields(query)
    is_comparative = len(entities) >= 2 or any(k in query.lower() for k in ["compare", "versus", "vs", "difference"])

    return {
        "raw_query": query,
        "entities": entities,
        "fields": fields,
        "is_comparative": is_comparative,
        "entity_count": len(entities),
        "field_count": len(fields)
    }
