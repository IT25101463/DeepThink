"""
Adaptive Context Budgeting & Dynamic Score Drop-Off Engine (Industry Standard)
Implements:
1. Intent-Based Context Budgeting (Sizes K based on query complexity)
2. Relative Score Drop-Off ("Elbow Method" / Knee-of-the-curve pruning)
3. Token Window Density Packing (Capped prompt context)
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("deepthink.adaptive_budget")

# Default budget ceilings
DEFAULT_MIN_K = 1
DEFAULT_MAX_K = 8
DEFAULT_ALPHA_DROPOFF = 0.60  # Keep chunks with score >= 60% of top chunk score
DEFAULT_MAX_TOKEN_BUDGET = 2500


def determine_query_intent_and_budget(
    query: str,
    entities: Optional[List[str]] = None,
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Classifies query complexity and determines the optimal initial chunk budget K.
    """
    q_lower = query.lower().strip()
    
    # Check visual / diagram intent
    visual_keywords = ["diagram", "blueprint", "schematic", "figure plate", "plate", "drawing", "illustration", "image", "photo", "map"]
    is_visual = any(re.search(r"\b" + re.escape(v) + r"\b", q_lower) for v in visual_keywords)
    
    # Check single-fact / date / number intent
    single_fact_keywords = ["when was", "what year", "birth year", "who is", "who was", "where was", "born in", "died in"]
    is_single_fact = any(q_lower.startswith(k) or k in q_lower for k in single_fact_keywords) and not ("compare" in q_lower or "difference" in q_lower)

    # Check comparative intent
    ent_count = len(entities) if entities else 0
    is_comparative = ent_count >= 2 or any(k in q_lower for k in ["compare", "versus", "vs", "difference between"])

    # Check quantitative / table aggregation
    quant_keywords = ["total", "sum", "average", "calculate", "how many", "count", "aggregate", "ledger", "budget"]
    is_quantitative = any(re.search(r"\b" + re.escape(k) + r"\b", q_lower) for k in quant_keywords)

    # Check multi-hop relational intent
    multi_hop_keywords = ["mentor of", "successor of", "commander of", "who signed", "after the death of"]
    is_multi_hop = any(k in q_lower for k in multi_hop_keywords)

    # Budget Allocation
    if is_visual:
        intent = "visual"
        target_k = 2
        min_k = 1
    elif is_single_fact:
        intent = "single_fact"
        target_k = 2
        min_k = 1
    elif is_comparative:
        intent = "comparative"
        # Minimum 3 chunks per compared entity
        target_k = min(DEFAULT_MAX_K, max(6, ent_count * 3))
        min_k = 2
    elif is_quantitative or is_multi_hop:
        intent = "quantitative_or_multihop"
        target_k = 6
        min_k = 2
    else:
        intent = "standard_narrative"
        target_k = 4
        min_k = 2

    return {
        "intent": intent,
        "target_k": target_k,
        "min_k": min_k,
        "is_visual": is_visual,
        "is_comparative": is_comparative,
        "is_quantitative": is_quantitative
    }


def apply_relative_score_dropoff(
    chunks: List[Dict[str, Any]],
    alpha: float = DEFAULT_ALPHA_DROPOFF,
    min_k: int = DEFAULT_MIN_K,
    max_k: int = DEFAULT_MAX_K
) -> List[Dict[str, Any]]:
    """
    Applies the Elbow Method / Knee-of-the-Curve score drop-off.
    Keeps chunk i iff Score(i) >= alpha * Score(1).
    Guarantees at least min_k chunks (if available) and at most max_k chunks.
    """
    if not chunks:
        return []

    # Sort descending by relevance_score or raw_similarity
    sorted_chunks = sorted(
        chunks, 
        key=lambda x: float(x.get("relevance_score", 0.0) or x.get("raw_similarity", 0.0) or 0.0), 
        reverse=True
    )

    top_score = float(sorted_chunks[0].get("relevance_score", 0.0) or sorted_chunks[0].get("raw_similarity", 0.0) or 0.0)
    
    # If top score is 0 or very low, fallback to top candidate
    if top_score <= 0.0:
        return sorted_chunks[:min_k]

    threshold = top_score * alpha
    retained = []

    for i, c in enumerate(sorted_chunks):
        c_score = float(c.get("relevance_score", 0.0) or c.get("raw_similarity", 0.0) or 0.0)
        
        # Always retain up to min_k
        if i < min_k:
            retained.append(c)
            continue

        # Stop when reaching max_k
        if len(retained) >= max_k:
            break

        # Check relative drop-off threshold
        if c_score >= threshold:
            retained.append(c)
        else:
            # Score dropped below relative threshold: drop trailing chunks
            logger.debug(f"Drop-off triggered at chunk {i+1}: score {c_score:.3f} < threshold {threshold:.3f}")
            break

    return retained


def apply_token_budget_packing(
    chunks: List[Dict[str, Any]],
    max_tokens: int = DEFAULT_MAX_TOKEN_BUDGET
) -> List[Dict[str, Any]]:
    """
    Packs context chunks up to the maximum token ceiling to guarantee fast inference.
    """
    packed = []
    current_tokens = 0

    for c in chunks:
        content_text = str(c.get("content", "")) + " " + str(c.get("caption", "") or "")
        # Heuristic: 1 word ≈ 1.33 tokens
        word_count = len(content_text.split())
        est_tokens = max(int(word_count * 1.33), 10)

        if packed and (current_tokens + est_tokens > max_tokens):
            logger.debug(f"Token budget reached ({current_tokens} tokens). Capping chunk list.")
            break

        packed.append(c)
        current_tokens += est_tokens

    return packed
