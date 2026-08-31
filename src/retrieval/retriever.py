"""
Modality-Aware Retriever Module (Owner: Member P3 - Team Leader)
Queries local ChromaDB vector store, analyzes query intent, applies dynamic
modality score boosting (W_modality), and returns top-k multimodal chunks for the LLM.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import (
    CHROMA_PERSIST_DIR, 
    DEFAULT_TOP_K, 
    MODALITY_BOOST_FACTOR,
    PROJECT_ROOT
)
from src.retrieval.indexer import get_embedding_function
from src.retrieval.router import analyze_query_intent

_CHROMA_CLIENT = None
_CHROMA_COLLECTION = None


def get_collection(collection_name: str = "ashen_era_chunks"):
    """
    Returns cached ChromaDB collection instance for fast query latency.
    """
    global _CHROMA_CLIENT, _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is None:
        try:
            import chromadb
        except ImportError:
            print("[Warning] chromadb is not installed. Please run: pip install chromadb")
            return None
            
        if not CHROMA_PERSIST_DIR.exists():
            CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            
        _CHROMA_CLIENT = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        embedding_fn = get_embedding_function()
        _CHROMA_COLLECTION = _CHROMA_CLIENT.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
    return _CHROMA_COLLECTION


def retrieve(
    query: str, 
    top_k: int = DEFAULT_TOP_K,
    collection_name: str = "ashen_era_chunks",
    modality_override: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k context chunks with modality-aware re-ranking.
    
    1. Detects query intent (Visual / Tabular / Text).
    2. Queries ChromaDB for top candidate vectors.
    3. Multiplies cosine similarity by W_modality boost factor.
    4. Returns deduplicated top-k chunks with metadata and relevance scores.
    """
    if not query or not query.strip():
        return []

    collection = get_collection(collection_name)
    if collection is None:
        return []
        
    total_docs = collection.count()
    if total_docs == 0:
        print("[Retriever Warning] ChromaDB collection is empty. Run 'python -m src.retrieval.indexer' first.")
        return []

    # 1. Analyze Intent
    intent_data = analyze_query_intent(query)
    target_modality = modality_override or intent_data["target_modality"]
    boost_weight = intent_data["boost_weight"] if not modality_override else MODALITY_BOOST_FACTOR

    # 2. Query candidates from ChromaDB
    fetch_k = min(max(top_k * 3, 15), total_docs)
    results = collection.query(
        query_texts=[query],
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"]
    )

    if not results or not results["ids"] or len(results["ids"][0]) == 0:
        return []

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    # 3. Apply Modality-Aware Re-ranking
    scored_chunks = []
    for c_id, content, meta, dist in zip(ids, docs, metas, distances):
        # Convert cosine distance to cosine similarity (range ~ 0.0 to 1.0)
        raw_sim = max(0.0, 1.0 - float(dist))
        modality = str(meta.get("modality", "text"))
        
        # Apply modality boost
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

    # 4. Sort by boosted relevance score descending
    scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)

    # 5. Return top-k
    return scored_chunks[:top_k]


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
