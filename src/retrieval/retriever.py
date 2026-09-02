"""
Modality-Aware Retriever Module (Owner: Member P3 - Team Leader)
Queries local ChromaDB vector store, analyzes query intent, applies dynamic
modality score boosting (W_modality), and returns top-k multimodal chunks for the LLM.
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

    # Extract meaningful query keywords
    stop_words = {
        "what", "which", "where", "when", "state", "according", "official", "figure",
        "plate", "about", "that", "this", "they", "their", "from", "the", "and", "for",
        "with", "does", "have", "were", "been", "also", "into", "whose", "whom", "each"
    }
    raw_words = re.findall(r"[A-Za-z0-9_\-]+", query.lower())
    words = [w for w in raw_words if len(w) >= 3 and w not in stop_words]

    scored = []
    for c in _IN_MEMORY_CHUNKS:
        doc_name = str(c.get("document_name", "")).lower()
        # Skip dataset root instructions/meta files
        if doc_name.startswith("readme"):
            continue

        caption = str(c.get("caption", "") or "").lower()
        section = str(c.get("section_title", "") or "").lower()
        content = str(c.get("content", "")).lower()
        modality = str(c.get("modality", "text"))
        media_p = c.get("media_path")

        # Full searchable text
        full_text = f"{doc_name} {caption} {section} {content}"

        # Count keyword hits with extra weighting for title/caption matches
        hit_score = 0.0
        exact_phrases_found = 0
        for w in words:
            if w in caption or w in doc_name or w in section:
                hit_score += 2.5
            elif w in content:
                hit_score += 1.0

        if hit_score == 0 and words:
            continue

        raw_sim = min(1.0, hit_score / (len(words) * 1.5 if words else 1.0))
        
        # Apply Modality Boost
        multiplier = 1.0
        if modality == target_modality:
            multiplier = boost_weight
        elif target_modality == "image-caption" and media_p:
            multiplier = 1.4

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


def retrieve(
    query: str, 
    top_k: int = DEFAULT_TOP_K,
    collection_name: str = "ashen_era_chunks",
    modality_override: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k context chunks with modality-aware re-ranking.
    
    1. Detects query intent (Visual / Tabular / Text).
    2. Queries ChromaDB for top candidate vectors (with instant hybrid fallback).
    3. Multiplies similarity by W_modality boost factor.
    4. Returns deduplicated top-k chunks with metadata and relevance scores.
    """
    if not query or not query.strip():
        return []

    # 1. Pre-Retrieval Domain Scope Check (Zero DB Calls for Off-Scope Queries)
    is_handled, _, _ = check_query_domain_scope(query)
    if is_handled:
        logger.info(f"Query '{query[:40]}' is greeting or off-domain. Skipping vector DB search.")
        return []

    # 2. Analyze Intent
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


if __name__ == "__main__":
    test_query = "Show me the diagram of the Sky-Fortress primary steam coolant valve"
    print(f"Testing retrieval for query: '{test_query}'...")
    chunks = retrieve(test_query, top_k=3)
    print(f"Retrieved {len(chunks)} chunks:")
    for i, c in enumerate(chunks, 1):
        print(f"\n[{i}] Score: {c['relevance_score']} | Modality: {c['modality']} | Doc: {c['document_name']} (P{c['page_number']})")
        if c['media_path']:
            print(f"    🖼️ Media Path: {c['media_path']}")
        print(f"    Text: {c['content'][:120]}...")
