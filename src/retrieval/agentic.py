"""
Agentic Query Decomposer & Multi-Hop Orchestrator (RAG 3.0)
Analyzes query complexity, decomposes multi-hop & comparative questions into atomic sub-queries,
and coordinates multi-step iterative retrieval.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("deepthink.agentic")

# Patterns indicating comparative and multi-hop questions
COMPARATIVE_PATTERNS = [
    r"\b(compare|comparison|difference between|versus|vs\.?|which is (better|larger|faster|heavier|stronger))\b",
    r"\b(both\s+.+?\s+and\s+.+?)\b",
    r"\b(.+?\s+compared to\s+.+?)\b"
]

MULTI_HOP_PATTERNS = [
    r"\b(mentor of|father of|son of|successor of|founder of|commander who|signatory of|ruler after|leader before)\b",
    r"\b(who (signed|built|designed|founded|led)\s+.+?\s+and (where|when|why|who))\b",
    r"\b(what happened (after|before)\s+.+?\s+(signed|occurred|fell))\b"
]

QUANTITATIVE_PATTERNS = [
    r"\b(total|sum of|average|combined|overall count|how many in total|calculate total|aggregate)\b",
    r"\b(cost breakdown|budget total|all expenditures|tally of)\b"
]

GLOBAL_SUMMARY_PATTERNS = [
    r"\b(all (battles|factions|treaties|weapons|artifacts|locations)|entire history|overview of all|chronology of)\b",
    r"\b(main themes|recurring themes|summary of the ashen era|comprehensive timeline)\b"
]


def is_complex_query(query: str) -> Tuple[bool, str]:
    """
    Classifies whether a query requires RAG 3.0 multi-hop / agentic handling.
    Returns (is_complex, complexity_type).
    """
    if not query or not query.strip():
        return False, "simple"

    q_lower = query.lower().strip()

    for p in COMPARATIVE_PATTERNS:
        if re.search(p, q_lower):
            return True, "comparative"

    for p in MULTI_HOP_PATTERNS:
        if re.search(p, q_lower):
            return True, "multi_hop"

    for p in QUANTITATIVE_PATTERNS:
        if re.search(p, q_lower):
            return True, "quantitative"

    for p in GLOBAL_SUMMARY_PATTERNS:
        if re.search(p, q_lower):
            return True, "global_summary"

    return False, "simple"


def decompose_query(query: str) -> List[str]:
    """
    Decomposes a complex query into atomic sub-questions for multi-step retrieval.
    """
    q_clean = query.strip()
    q_lower = q_clean.lower()
    is_complex, q_type = is_complex_query(q_clean)

    if not is_complex:
        return [q_clean]

    from src.retrieval.entity_matcher import analyze_query_structure

    q_struct = analyze_query_structure(q_clean)
    entities = q_struct["entities"]
    fields = q_struct["fields"]
    fields_str = " ".join(fields) if fields else "specifications details"
    sub_queries = [q_clean]

    # 1. Comparative Query Decomposition (Multi-Entity & Multi-Field Coverage)
    if q_type == "comparative" or len(entities) >= 2:
        if len(entities) >= 2:
            for ent in entities:
                sub_queries.append(f"{ent} {fields_str}")
        else:
            match_compare = re.search(r"(?:compare|difference between)\s+(.+?)\s+(?:and|with|to)\s+(.+?)(?:\?|$)", q_clean, re.IGNORECASE)
            if match_compare:
                ent1 = match_compare.group(1).strip()
                ent2 = match_compare.group(2).strip()
                sub_queries.append(f"{ent1} {fields_str}")
                sub_queries.append(f"{ent2} {fields_str}")

    # 2. Multi-Hop Relational Query Decomposition
    elif q_type == "multi_hop":
        # Look for relational chains (e.g., "mentor of X who signed Y")
        match_rel = re.search(r"(mentor|successor|founder|leader|commander)\s+of\s+(.+?)(?:\s+who|\s+and|\?|$)", q_clean, re.IGNORECASE)
        if match_rel:
            rel_type = match_rel.group(1).strip()
            subject = match_rel.group(2).strip()
            sub_queries.append(f"Who is the {rel_type} of {subject}?")
            sub_queries.append(f"{subject} {rel_type} history background")
        else:
            sub_queries.append(q_clean)

    # 3. Quantitative / Table Aggregation
    elif q_type == "quantitative":
        sub_queries.append(q_clean)
        sub_queries.append(f"table ledger {fields_str} {q_clean}")

    # 4. Global Summary Query
    elif q_type == "global_summary":
        sub_queries.append(q_clean)
        sub_queries.append("annals chronicle overview summary")

    if not sub_queries:
        sub_queries = [q_clean]

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for sq in sub_queries:
        if sq.lower() not in seen:
            seen.add(sq.lower())
            deduped.append(sq)

    return deduped


def agentic_retrieve(
    query: str,
    base_retriever_fn,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Executes multi-step iterative retrieval:
    1. Decomposes query into sub-questions.
    2. Retrieves candidate chunks for each sub-question.
    3. Fuses, cross-deduplicates, and re-ranks evidence across hops.
    """
    sub_queries = decompose_query(query)
    
    if len(sub_queries) <= 1:
        # Standard retrieval
        return base_retriever_fn(query, top_k=top_k)

    logger.info(f"RAG 3.0 Agentic Decomposition: {len(sub_queries)} sub-queries generated for '{query[:40]}'")
    
    collected_chunks: Dict[str, Dict[str, Any]] = {}
    sub_k = max(3, (top_k // len(sub_queries)) + 2)

    for i, sub_q in enumerate(sub_queries, 1):
        logger.debug(f"Executing sub-query [{i}/{len(sub_queries)}]: '{sub_q}'")
        sub_results = base_retriever_fn(sub_q, top_k=sub_k)
        
        for chunk in sub_results:
            c_id = chunk.get("chunk_id") or f"{chunk.get('document_name')}_{chunk.get('page_number')}"
            if c_id not in collected_chunks:
                # Add agentic sub-query provenance tag
                chunk_copy = dict(chunk)
                chunk_copy["retrieved_via_subquery"] = sub_q
                chunk_copy["multi_hop_step"] = i
                collected_chunks[c_id] = chunk_copy
            else:
                # If chunk was retrieved by multiple sub-queries, boost its relevance
                existing = collected_chunks[c_id]
                existing["relevance_score"] = round(existing.get("relevance_score", 0.5) * 1.25, 4)
                existing["multi_hop_corroboration"] = True

    merged_list = list(collected_chunks.values())
    merged_list.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
    
    return merged_list[:top_k]
