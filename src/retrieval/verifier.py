"""
Pre-Generation Context & Relevance Verifier
Performs multi-step validation:
1. Matches queried entities against each retrieved chunk.
2. Verifies presence of all requested comparison fields.
3. Filters out individual unrelated/distractor chunks before generation.
4. Rejects the entire result if the context is insufficient or off-topic.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional

from src.retrieval.entity_matcher import analyze_query_structure, KNOWN_FIELDS

logger = logging.getLogger("deepthink.verifier")


def check_chunk_entity_match(chunk: Dict[str, Any], entity: str) -> bool:
    """
    Checks if a chunk contains the specific entity using word boundary, phrase matching, and stemming.
    """
    if not entity:
        return True

    text_corpus = " ".join([
        str(chunk.get("content", "")),
        str(chunk.get("caption", "") or ""),
        str(chunk.get("document_name", "")),
        str(chunk.get("section_title", "") or "")
    ]).lower()

    e_clean = entity.lower().strip()
    if e_clean in text_corpus:
        return True

    # Check singular/stem variants (e.g. "units" -> "unit", "ballistas" -> "ballista")
    stem = e_clean[:-1] if (e_clean.endswith("s") and len(e_clean) > 3) else e_clean
    if stem in text_corpus or (e_clean + "s") in text_corpus:
        return True

    e_tokens = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", e_clean)]
    if e_tokens:
        tok_matches = 0
        for tok in e_tokens:
            tok_stem = tok[:-1] if (tok.endswith("s") and len(tok) > 3) else tok
            if (re.search(r"\b" + re.escape(tok) + r"\b", text_corpus) or 
                re.search(r"\b" + re.escape(tok_stem) + r"\b", text_corpus)):
                tok_matches += 1
        if tok_matches == len(e_tokens):
            return True

    return False


def check_chunk_field_match(chunk: Dict[str, Any], field: str) -> bool:
    """
    Checks if a chunk contains terms related to a specific requested attribute field.
    """
    aliases = KNOWN_FIELDS.get(field, [field])
    text_corpus = " ".join([
        str(chunk.get("content", "")),
        str(chunk.get("caption", "") or ""),
        str(chunk.get("section_title", "") or "")
    ]).lower()

    for alias in aliases:
        if re.search(r"\b" + re.escape(alias) + r"\b", text_corpus):
            return True

    return False


def verify_and_filter_context(
    query: str, 
    retrieved_chunks: List[Dict[str, Any]],
    strict_entity_matching: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Verifies retrieved context, prunes unrelated chunks, and measures entity & field coverage.
    
    Returns:
    - filtered_chunks: only high-relevance chunks that mention queried entities/fields.
    - verification_report: metadata dict with entity coverage, field coverage, and sufficiency verdict.
    """
    if not retrieved_chunks:
        return [], {
            "is_sufficient": False,
            "rejection_reason": "No context chunks retrieved from archive.",
            "entity_coverage": {},
            "field_coverage": {},
            "retained_count": 0,
            "pruned_count": 0
        }

    q_struct = analyze_query_structure(query)
    entities = q_struct["entities"]
    fields = q_struct["fields"]
    is_comparative = q_struct["is_comparative"]

    filtered_chunks = []
    pruned_chunks = []

    # 1. Per-chunk relevance filter
    for chunk in retrieved_chunks:
        raw_sim = float(chunk.get("raw_similarity", 0.5) or 0.5)
        rel_score = float(chunk.get("relevance_score", 0.5) or 0.5)
        modality = str(chunk.get("modality", "text"))
        is_table = modality == "table" or "|" in str(chunk.get("content", ""))

        # Check if chunk matches at least one target entity
        has_entity_match = False
        matched_entity_names = []
        if entities:
            for ent in entities:
                if check_chunk_entity_match(chunk, ent):
                    has_entity_match = True
                    matched_entity_names.append(ent)
        else:
            # General query without named entities
            has_entity_match = True

        # Check field matches
        matched_field_names = []
        if fields:
            for f in fields:
                if check_chunk_field_match(chunk, f):
                    matched_field_names.append(f)

        # Allow tables if they match requested fields even if entity was generic
        if is_table and fields and len(matched_field_names) > 0:
            has_entity_match = True

        # Pruning decision:
        # If strict entity matching is active and query has specific entities,
        # reject chunks that mention ZERO queried entities.
        if strict_entity_matching and entities and not has_entity_match:
            pruned_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "document_name": chunk.get("document_name"),
                "reason": f"Chunk did not contain queried entities: {entities}"
            })
            continue

        chunk_copy = dict(chunk)
        chunk_copy["verified_entities"] = matched_entity_names
        chunk_copy["verified_fields"] = matched_field_names
        filtered_chunks.append(chunk_copy)

    # For general queries without specific entities, if filtered_chunks is empty, keep top candidate if similarity is high
    if not filtered_chunks and retrieved_chunks and not entities:
        top_cand = retrieved_chunks[0]
        if float(top_cand.get("raw_similarity", 0.0) or 0.0) >= 0.55:
            filtered_chunks.append(top_cand)

    # 2. Entity Coverage Verification
    entity_coverage = {}
    for ent in entities:
        matching_count = sum(1 for c in filtered_chunks if ent in c.get("verified_entities", []))
        entity_coverage[ent] = {
            "found": matching_count > 0,
            "matching_chunks": matching_count
        }

    # 3. Field Coverage Verification
    field_coverage = {}
    for f in fields:
        matching_count = sum(1 for c in filtered_chunks if f in c.get("verified_fields", []))
        field_coverage[f] = {
            "found": matching_count > 0,
            "matching_chunks": matching_count
        }

    # 4. Overall Sufficiency Verdict
    is_sufficient = True
    rejection_reason = None

    if not filtered_chunks:
        is_sufficient = False
        rejection_reason = f"No archival records found matching entity '{', '.join(entities)}'."
    elif entities and is_comparative:
        missing_entities = [ent for ent, data in entity_coverage.items() if not data["found"]]
        if len(missing_entities) == len(entities):
            is_sufficient = False
            rejection_reason = f"Archival records missing for both entities: {', '.join(missing_entities)}."
    elif entities and not any(data["found"] for data in entity_coverage.values()):
        # Check if table/field match covers the query
        has_field_match = any(data["found"] for data in field_coverage.values())
        has_table_chunk = any(c.get("modality") == "table" or "|" in str(c.get("content", "")) for c in filtered_chunks)
        if not (has_table_chunk and has_field_match):
            is_sufficient = False
            rejection_reason = f"Queried entity '{entities[0]}' not present in retrieved archival documents."

    report = {
        "is_sufficient": is_sufficient,
        "rejection_reason": rejection_reason,
        "entity_coverage": entity_coverage,
        "field_coverage": field_coverage,
        "is_comparative": is_comparative,
        "retained_count": len(filtered_chunks),
        "pruned_count": len(pruned_chunks),
        "pruned_details": pruned_chunks
    }

    return filtered_chunks, report
