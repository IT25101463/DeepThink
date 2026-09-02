"""
Precision Re-Ranker Module (RAG 3.0)
Performs second-stage re-ranking over candidate chunks to eliminate keyword distractors,
solve the 'Lost in the Middle' problem, and bubble up the highest-value evidence.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("deepthink.reranker")


def compute_cross_relevance(query: str, chunk: Dict[str, Any]) -> float:
    """
    Computes a composite cross-attention relevance score between query and chunk:
    - Entity co-occurrence & exact phrase presence
    - Modality alignment
    - Caption / Header matches
    - Content density & reliability score
    """
    q_clean = query.lower().strip()
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", q_clean)
    
    stop_words = {
        "what", "which", "where", "when", "who", "whom", "whose", "why", "how",
        "the", "and", "for", "with", "about", "that", "this", "from", "into", "details"
    }
    keywords = [w for w in raw_tokens if w not in stop_words]

    from src.retrieval.entity_matcher import analyze_query_structure, KNOWN_FIELDS

    q_struct = analyze_query_structure(query)
    entities = [e.lower() for e in q_struct["entities"]]
    fields = q_struct["fields"]

    content = str(chunk.get("content", "")).lower()
    doc_name = str(chunk.get("document_name", "")).lower()
    caption = str(chunk.get("caption", "") or "").lower()
    section = str(chunk.get("section_title", "") or "").lower()
    modality = str(chunk.get("modality", "text"))
    full_text = f"{doc_name} {caption} {section} {content}"

    # 1. Exact Entity Matching Bonus & Multi-Entity Intersection
    entity_bonus = 0.0
    has_entity_hit = False
    matched_entities_count = 0
    if entities:
        for ent in entities:
            if ent in full_text:
                entity_bonus += 0.50
                has_entity_hit = True
                matched_entities_count += 1
            else:
                ent_toks = [t for t in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", ent) if t not in stop_words]
                if ent_toks and all(re.search(r"\b" + re.escape(t) + r"\b", full_text) for t in ent_toks):
                    entity_bonus += 0.35
                    has_entity_hit = True
                    matched_entities_count += 1

    # Bonus for chunks spanning MULTIPLE queried entities (e.g. Person X + Faction Y)
    if matched_entities_count >= 2:
        entity_bonus += 0.40

    # Dedicated Dossier Bonus: if document_name directly matches any queried entity
    dossier_bonus = 0.0
    if entities:
        for ent in entities:
            ent_norm = ent.replace(" ", "_").replace("-", "_")
            doc_norm = doc_name.replace("-", "_")
            if ent_norm in doc_norm:
                dossier_bonus += 0.35
                break

    # 2. Field Match Bonus
    field_bonus = 0.0
    if fields:
        for f in fields:
            aliases = KNOWN_FIELDS.get(f, [f])
            if any(re.search(r"\b" + re.escape(a) + r"\b", full_text) for a in aliases):
                field_bonus += 0.25

    # 3. Keyword coverage ratio
    if not keywords:
        kw_coverage = 0.5
    else:
        found_kw = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", full_text))
        kw_coverage = found_kw / len(keywords)

    # 4. Phrase match bonus (exact multi-word sequence match)
    phrase_bonus = 0.0
    if len(keywords) >= 2:
        phrase = " ".join(keywords[:3])
        if phrase in content or phrase in caption:
            phrase_bonus = 0.35

    # 5. Base vector / initial relevance score
    base_score = float(chunk.get("relevance_score", 0.5) or 0.5)
    raw_sim = float(chunk.get("raw_similarity", 0.5) or 0.5)

    # 6. Modality & Media boost
    modality_bonus = 0.0
    if chunk.get("media_path") and modality in ("image-caption", "table"):
        modality_bonus = 0.15

    # 7. Reliability weighting
    reliability = str(chunk.get("source_reliability", "archive_record")).lower()
    rel_multiplier = 1.0
    if "official" in reliability or "codex" in reliability:
        rel_multiplier = 1.1
    elif "unverified" in reliability or "ballad" in reliability:
        rel_multiplier = 0.85

    # Penalty for 0 entity matches when entities were queried
    entity_penalty = 0.2 if (entities and not has_entity_hit and len(keywords) > 0) else 1.0

    # Composite cross-relevance calculation
    cross_score = (
        (base_score * 0.25) +
        (raw_sim * 0.20) +
        (kw_coverage * 0.25) +
        entity_bonus +
        dossier_bonus +
        field_bonus +
        phrase_bonus +
        modality_bonus
    ) * rel_multiplier * entity_penalty

    return round(cross_score, 4)


def rerank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Re-ranks candidate chunks using cross-relevance scoring.
    """
    if not chunks:
        return []

    if len(chunks) == 1:
        return chunks

    reranked = []
    for c in chunks:
        c_copy = dict(c)
        score = compute_cross_relevance(query, c)
        c_copy["rerank_score"] = score
        c_copy["relevance_score"] = score
        reranked.append(c_copy)

    # Sort descending by rerank score
    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    logger.debug(f"Re-ranked {len(chunks)} candidate chunks for query: '{query[:40]}'")
    return reranked[:top_k]
