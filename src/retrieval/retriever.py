"""
Modality-Aware Retriever Module (Owner: Member P3 - Team Leader)
Queries local ChromaDB vector store, analyzes query intent, applies dynamic
modality score boosting (W_modality), executes Corrective RAG (CRAG) confidence grading,
and returns top-k multimodal chunks for the LLM.
Includes fast in-memory hybrid search fallback when ChromaDB is unindexed or initializing.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import (
    CHROMA_PERSIST_DIR, 
    DEFAULT_TOP_K, 
    MODALITY_BOOST_FACTOR,
    PROJECT_ROOT,
    CHUNKS_JSON_PATH
)
from src.retrieval.router import analyze_query_intent, check_query_domain_scope

logger = logging.getLogger("deepthink.retriever")

_CHROMA_CLIENT = None
_CHROMA_COLLECTION = None
_IN_MEMORY_CHUNKS = None


def get_collection(collection_name: str = "ashen_era_chunks"):
    """
    Returns cached ChromaDB collection instance for fast query latency.
    """
    global _CHROMA_CLIENT, _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is None:
        if not (CHROMA_PERSIST_DIR.exists() and any(CHROMA_PERSIST_DIR.iterdir())):
            return None

        try:
            import chromadb
            from src.retrieval.indexer import get_embedding_function
            
            _CHROMA_CLIENT = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
            embedding_fn = get_embedding_function()
            if embedding_fn is None:
                return None
            _CHROMA_COLLECTION = _CHROMA_CLIENT.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB ({e}). Utilizing fast in-memory search fallback.")
            return None
            
    return _CHROMA_COLLECTION


def evaluate_retrieval_confidence(
    query: str, 
    retrieved_chunks: List[Dict[str, Any]], 
    threshold: float = 0.28
) -> Dict[str, Any]:
    """
    Universal Corrective RAG (CRAG) & Out-of-Distribution (OOD) Evaluator:
    Mathematically measures vector space distance and cross-corpus entity overlap
    WITHOUT relying on hardcoded keyword blacklists.
    
    Verdicts:
    - 'CORRECT': In-domain, high relevance (top_sim >= 0.45 and entities present).
    - 'AMBIGUOUS': In-domain, partial context (0.28 <= top_sim < 0.45).
    - 'OUT_OF_DOMAIN': Mathematically out-of-distribution (top_sim < 0.28 or 0% entity presence on specific terms).
    """
    if not retrieved_chunks:
        return {
            "verdict": "OUT_OF_DOMAIN",
            "is_in_domain": False,
            "confidence_score": 0.0,
            "top_similarity": 0.0,
            "matched_entities": [],
            "overlap_ratio": 0.0,
            "reason": "No vector space match found in corpus."
        }

    top_chunk = retrieved_chunks[0]
    top_sim = float(top_chunk.get("raw_similarity", 0.0) or 0.0)
    relevance_score = float(top_chunk.get("relevance_score", 0.0) or 0.0)

    # Universal Stopwords to isolate domain-specific content nouns
    stop_words = {
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
        "please", "could", "would", "look", "like", "details", "information", "record"
    }
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query.lower())
    query_nouns = [w for w in raw_tokens if w not in stop_words]
    
    # Inspect top 5 chunks for cross-corpus entity presence
    combined_chunk_text = " ".join([
        f"{c.get('content', '')} {c.get('document_name', '')} {c.get('caption', '')} {c.get('section_title', '')}".lower()
        for c in retrieved_chunks[:5]
    ])

    matched_nouns = [w for w in query_nouns if w in combined_chunk_text]
    overlap_ratio = len(matched_nouns) / max(len(query_nouns), 1)

    # Combined Metric (Cosine Similarity + Lexical Entity Overlap)
    confidence = round((top_sim * 0.6) + (overlap_ratio * 0.4), 4)

    # Universal OOD Decision Logic (Mathematical Confidence & Entity Grounding)
    if not query_nouns:
        # Generic or stopword-only query without specific entities
        is_in_domain = top_sim >= threshold
        verdict = "CORRECT" if top_sim >= 0.45 else ("AMBIGUOUS" if is_in_domain else "OUT_OF_DOMAIN")
        reason = "Generic query evaluated via vector similarity manifold."
    elif len(matched_nouns) == 0 and (top_sim < 0.40 or len(query_nouns) >= 2):
        # 0% entity presence across top chunks and weak similarity -> OOD
        verdict = "OUT_OF_DOMAIN"
        is_in_domain = False
        reason = f"Zero domain entities found in corpus for query keywords: {query_nouns[:4]}."
    elif top_sim < threshold and overlap_ratio < 0.25:
        # Cosine distance mathematically outside corpus distribution -> OOD
        verdict = "OUT_OF_DOMAIN"
        is_in_domain = False
        reason = f"Low vector similarity ({top_sim}) and low entity overlap ({overlap_ratio})."
    elif top_sim >= 0.45 and (overlap_ratio >= 0.20 or len(matched_nouns) >= 1):
        verdict = "CORRECT"
        is_in_domain = True
        reason = "High vector similarity and verified domain entity overlap."
    elif top_sim >= threshold and overlap_ratio >= 0.20:
        verdict = "AMBIGUOUS"
        is_in_domain = True
        reason = "Moderate vector similarity with matching domain entities."
    elif confidence >= 0.35 and len(matched_nouns) >= 1:
        verdict = "AMBIGUOUS"
        is_in_domain = True
        reason = "Sufficient combined confidence score with entity match."
    else:
        verdict = "OUT_OF_DOMAIN"
        is_in_domain = False
        reason = "Insufficient confidence and entity overlap."

    return {
        "verdict": verdict,
        "is_in_domain": is_in_domain,
        "confidence_score": confidence,
        "top_similarity": top_sim,
        "matched_entities": matched_nouns,
        "overlap_ratio": round(overlap_ratio, 2),
        "reason": reason
    }


def _retrieve_in_memory_fallback(
    query: str, 
    target_modality: str, 
    boost_weight: float, 
    top_k: int
) -> List[Dict[str, Any]]:
    """
    Fast, highly accurate in-memory fallback search over data/chunks.json
    when ChromaDB is not yet populated or offline.
    """
    global _IN_MEMORY_CHUNKS
    if _IN_MEMORY_CHUNKS is None:
        if CHUNKS_JSON_PATH.exists():
            try:
                with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
                    _IN_MEMORY_CHUNKS = json.load(f)
            except Exception as e:
                logger.error(f"Error loading chunks.json: {e}")
                _IN_MEMORY_CHUNKS = []
        else:
            _IN_MEMORY_CHUNKS = []

    if not _IN_MEMORY_CHUNKS:
        return []

    from src.retrieval.entity_matcher import analyze_query_structure, KNOWN_FIELDS

    q_struct = analyze_query_structure(query)
    entities = [e.lower() for e in q_struct["entities"]]
    fields = q_struct["fields"]
    
    stop_words = {
        "what", "which", "where", "when", "state", "according", "official", "figure",
        "plate", "about", "that", "this", "they", "their", "from", "the", "and", "for",
        "with", "does", "have", "were", "been", "also", "into", "whose", "whom", "each",
        "details", "information", "record", "records", "document", "annals", "tell", "show"
    }
    raw_words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query.lower())
    general_words = [w for w in raw_words if w not in stop_words]

    scored = []
    for c in _IN_MEMORY_CHUNKS:
        doc_name = str(c.get("document_name", "")).lower()
        if doc_name.startswith("readme"):
            continue

        caption = str(c.get("caption", "") or "").lower()
        section = str(c.get("section_title", "") or "").lower()
        content = str(c.get("content", "")).lower()
        modality = str(c.get("modality", "text"))
        media_p = c.get("media_path")

        full_text = f"{doc_name} {caption} {section} {content}"

        # 1. Exact Entity Matching (Critical for entity accuracy)
        entity_hit_score = 0.0
        entities_matched = 0
        if entities:
            for ent in entities:
                # Exact entity phrase match
                if ent in full_text:
                    entity_hit_score += 8.0
                    entities_matched += 1
                else:
                    # Token-level entity match
                    ent_toks = [t for t in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", ent) if t not in stop_words]
                    if ent_toks:
                        tok_hits = sum(1 for t in ent_toks if re.search(r"\b" + re.escape(t) + r"\b", full_text))
                        if tok_hits == len(ent_toks):
                            entity_hit_score += 5.0
                            entities_matched += 1
                        elif tok_hits > 0:
                            entity_hit_score += tok_hits * 1.5

        # 2. Requested Field Matching (Critical for multi-field comparisons)
        field_hit_score = 0.0
        if fields:
            for f in fields:
                aliases = KNOWN_FIELDS.get(f, [f])
                if any(re.search(r"\b" + re.escape(a) + r"\b", full_text) for a in aliases):
                    field_hit_score += 3.0

        # 3. General Keyword Hits with Word Boundaries
        general_hit_score = 0.0
        for w in general_words:
            w_pattern = r"\b" + re.escape(w) + r"\b"
            if re.search(w_pattern, doc_name):
                general_hit_score += 2.0
            if re.search(w_pattern, caption):
                general_hit_score += 2.0
            if re.search(w_pattern, section):
                general_hit_score += 1.5
            if re.search(w_pattern, content):
                general_hit_score += 1.0

        total_hit_score = entity_hit_score + field_hit_score + general_hit_score
        if total_hit_score == 0:
            continue

        # Strict Entity Penalty: If query has specific entities but this chunk matches 0 of them, penalize
        if entities and entities_matched == 0 and len(general_words) > 0:
            total_hit_score *= 0.15

        # Normalized similarity
        max_possible = max((len(entities) * 8.0) + (len(fields) * 3.0) + (len(general_words) * 2.0), 1.0)
        raw_sim = min(1.0, total_hit_score / max_possible)

        # Apply Modality Boost Factor (W_modality)
        multiplier = 1.0
        if modality == target_modality:
            multiplier = boost_weight
        elif target_modality == "image-caption" and media_p:
            multiplier = 1.3

        final_score = raw_sim * multiplier

        meta = c.get("metadata", {}) if isinstance(c.get("metadata"), dict) else {}
        chunk_obj = {
            "chunk_id": c.get("chunk_id", ""),
            "document_name": c.get("document_name", "Unknown"),
            "document_type": c.get("document_type", "txt"),
            "page_number": int(c.get("page_number", 1) or 1),
            "section_title": c.get("section_title", ""),
            "modality": modality,
            "content": c.get("content", ""),
            "media_path": media_p if media_p else None,
            "caption": c.get("caption") if c.get("caption") else None,
            "raw_similarity": round(raw_sim, 4),
            "relevance_score": round(final_score, 4),
            "source_reliability": meta.get("source_reliability", "archive_record")
        }
        scored.append(chunk_obj)

    # Sort descending by relevance score
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored[:top_k]


def _retrieve_single_pass(
    query: str, 
    top_k: int = DEFAULT_TOP_K,
    collection_name: str = "ashen_era_chunks",
    modality_override: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes a single-pass hybrid retrieval over ChromaDB or in-memory fallback.
    """
    if not query or not query.strip():
        return []

    # Analyze Intent
    intent_data = analyze_query_intent(query)
    target_modality = modality_override or intent_data["target_modality"]
    boost_weight = intent_data["boost_weight"] if not modality_override else MODALITY_BOOST_FACTOR

    # Try ChromaDB first
    collection = get_collection(collection_name)
    if collection is not None:
        try:
            total_docs = collection.count()
            if total_docs > 0:
                fetch_k = min(max(top_k * 3, 15), total_docs)
                results = collection.query(
                    query_texts=[query],
                    n_results=fetch_k,
                    include=["documents", "metadatas", "distances"]
                )

                if results and results["ids"] and len(results["ids"][0]) > 0:
                    ids = results["ids"][0]
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    distances = results["distances"][0]

                    scored_chunks = []
                    for c_id, content, meta, dist in zip(ids, docs, metas, distances):
                        doc_name = str(meta.get("document_name", "")).lower()
                        if doc_name.startswith("readme"):
                            continue

                        raw_sim = max(0.0, 1.0 - float(dist))
                        modality = str(meta.get("modality", "text"))
                        
                        multiplier = 1.0
                        if modality == target_modality:
                            multiplier = boost_weight
                        elif target_modality == "image-caption" and meta.get("media_path"):
                            multiplier = 1.3
                            
                        final_score = raw_sim * multiplier
                        
                        chunk_obj = {
                            "chunk_id": c_id,
                            "document_name": meta.get("document_name", "Unknown"),
                            "document_type": meta.get("document_type", "txt"),
                            "page_number": int(meta.get("page_number", 1)),
                            "section_title": meta.get("section_title", ""),
                            "modality": modality,
                            "content": content,
                            "media_path": meta.get("media_path") if meta.get("media_path") else None,
                            "caption": meta.get("caption") if meta.get("caption") else None,
                            "raw_similarity": round(raw_sim, 4),
                            "relevance_score": round(final_score, 4),
                            "source_reliability": meta.get("source_reliability", "archive_record")
                        }
                        scored_chunks.append(chunk_obj)

                    scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
                    return scored_chunks[:top_k]
        except Exception as e:
            logger.debug(f"ChromaDB query encountered issue ({e}), using in-memory hybrid search.")

    # In-memory hybrid fallback
    return _retrieve_in_memory_fallback(query, target_modality, boost_weight, top_k)


def retrieve(
    query: str, 
    top_k: Optional[int] = None,
    collection_name: str = "ashen_era_chunks",
    modality_override: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    RAG 3.0 Compound & Adaptive Retriever (Industry Standard):
    1. Evaluates Pre-Retrieval Domain Scope.
    2. Adaptive Intent-Based Budgeting: Dynamically sizes candidate & final K.
    3. Executes Agentic Multi-Step Decomposition if complex.
    4. Precision Cross-Encoder Re-Ranking over candidate chunks.
    5. Pre-Generation Verification Gate (Prunes zero-entity distractors).
    6. Relative Score Drop-Off (Elbow / Knee Cutoff) to eliminate trailing noise.
    7. Token Budget Density Packing (Capped prompt context).
    """
    if not query or not query.strip():
        return []

    # 1. Pre-Retrieval Domain Scope Check
    is_handled, _, _ = check_query_domain_scope(query)
    if is_handled:
        logger.info(f"Query '{query[:40]}' is greeting or off-domain. Skipping vector DB search.")
        return []

    # 2. Extract Structure & Compute Adaptive Budget
    from src.retrieval.entity_matcher import analyze_query_structure
    from src.retrieval.adaptive_budget import (
        determine_query_intent_and_budget,
        apply_relative_score_dropoff,
        apply_token_budget_packing
    )

    q_struct = analyze_query_structure(query)
    budget = determine_query_intent_and_budget(
        query=query,
        entities=q_struct.get("entities"),
        fields=q_struct.get("fields")
    )

    effective_k = top_k if (top_k is not None and top_k != DEFAULT_TOP_K) else budget["target_k"]
    min_k = budget["min_k"]
    fetch_candidate_k = max(effective_k * 2, 10)

    # 3. Check Complexity & Execute Agentic Retrieval
    from src.retrieval.agentic import is_complex_query, agentic_retrieve
    from src.retrieval.reranker import rerank_chunks

    is_complex, q_type = is_complex_query(query)

    def base_lookup(q_sub: str, top_k: int = fetch_candidate_k):
        return _retrieve_single_pass(
            query=q_sub,
            top_k=top_k,
            collection_name=collection_name,
            modality_override=modality_override
        )

    if is_complex:
        logger.info(f"Complex query detected ({q_type}). Running agentic retrieval with target K={effective_k}.")
        candidates = agentic_retrieve(query, base_lookup, top_k=fetch_candidate_k)
    else:
        candidates = base_lookup(query, top_k=fetch_candidate_k)

    # 4. Apply Precision Second-Stage Re-Ranking
    final_ranked_chunks = rerank_chunks(query, candidates, top_k=fetch_candidate_k)

    # 5. Pre-Generation Context & Relevance Verification Gate
    from src.retrieval.verifier import verify_and_filter_context
    verified_chunks, _ = verify_and_filter_context(query, final_ranked_chunks)
    active_pool = verified_chunks if verified_chunks else final_ranked_chunks

    # 6. Relative Score Drop-Off ("Elbow Method" Pruning)
    dropoff_filtered = apply_relative_score_dropoff(
        chunks=active_pool,
        alpha=0.60,
        min_k=min_k,
        max_k=effective_k
    )

    # 7. Token Window Density Packing
    final_context = apply_token_budget_packing(dropoff_filtered, max_tokens=2500)
    return final_context


if __name__ == "__main__":
    test_query = "Show me the diagram of the Sky-Fortress primary steam coolant valve"
    print(f"Testing retrieval for query: '{test_query}'...")
    chunks = retrieve(test_query, top_k=3)
    print(f"Retrieved {len(chunks)} chunks:")
    for i, c in enumerate(chunks, 1):
        print(f"\n[{i}] Score: {c['relevance_score']} | Modality: {c['modality']} | Doc: {c['document_name']} (P{c['page_number']})")
        if c['media_path']:
            print(f"    Media: {c['media_path']}")

    crag_eval = evaluate_retrieval_confidence(test_query, chunks)
    print(f"\nCRAG Evaluation: {crag_eval}")
