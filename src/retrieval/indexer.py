"""
Vector Indexer Module (Owner: Member P3)
Embeds chunks from data/chunks.json using local HuggingFace BGE embeddings
and indexes them into a persistent local ChromaDB vector store.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

from src.config import (
    CHUNKS_JSON_PATH, 
    CHROMA_PERSIST_DIR, 
    EMBEDDING_MODEL_NAME
)


_CACHED_EMBEDDING_FN = None


def get_embedding_function():
    """
    Initializes and caches the local SentenceTransformer embedding function.
    Defaults to BAAI/bge-small-en-v1.5 (100% free, zero-card, zero-key).
    """
    global _CACHED_EMBEDDING_FN
    if _CACHED_EMBEDDING_FN is not None:
        return _CACHED_EMBEDDING_FN

    try:
        from chromadb.utils import embedding_functions
        _CACHED_EMBEDDING_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        return _CACHED_EMBEDDING_FN
    except ImportError:
        print("[Warning] chromadb or sentence_transformers not installed. Install via pip install -r requirements.txt")
        return None
    except Exception as e:
        print(f"[Warning] Failed to load '{EMBEDDING_MODEL_NAME}': {e}")
        print("Falling back to lightweight 'all-MiniLM-L6-v2'...")
        from chromadb.utils import embedding_functions
        _CACHED_EMBEDDING_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        return _CACHED_EMBEDDING_FN


def sanitize_metadata(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares metadata dictionary for ChromaDB.
    ChromaDB requires metadata values to be str, int, float, or bool.
    """
    meta = {
        "chunk_id": str(chunk.get("chunk_id", "")),
        "document_name": str(chunk.get("document_name", "Unknown")),
        "document_type": str(chunk.get("document_type", "txt")),
        "page_number": int(chunk.get("page_number", 1) or 1),
        "section_title": str(chunk.get("section_title", "") or ""),
        "modality": str(chunk.get("modality", "text") or "text"),
        "media_path": str(chunk.get("media_path", "") or ""),
        "caption": str(chunk.get("caption", "") or "")
    }
    
    # Store source reliability from nested metadata if present
    custom_meta = chunk.get("metadata", {})
    if isinstance(custom_meta, dict):
        if "source_reliability" in custom_meta:
            meta["source_reliability"] = str(custom_meta["source_reliability"])
        if "word_count" in custom_meta:
            meta["word_count"] = int(custom_meta["word_count"] or 0)
            
    return meta


def index_chunks(
    chunks_file: Path = CHUNKS_JSON_PATH,
    collection_name: str = "ashen_era_chunks",
    batch_size: int = 250,
    reset_collection: bool = False
):
    """
    Reads chunks.json, generates local BGE embeddings in batches, and indexes into ChromaDB.
    """
    try:
        import chromadb
    except ImportError:
        print("❌ Error: chromadb is not installed. Please run: pip install chromadb sentence-transformers")
        return

    if not chunks_file.exists():
        print(f"❌ Error: Chunks file not found at '{chunks_file}'.")
        print("Make sure data/chunks.json is present.")
        return

    print(f"📖 Reading chunks from: {chunks_file}")
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not isinstance(chunks, list) or len(chunks) == 0:
        print("❌ Error: Chunks file is empty or invalid format.")
        return

    print(f"🚀 Loaded {len(chunks)} chunks. Preparing local ChromaDB vector store...")
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    embedding_fn = get_embedding_function()

    if reset_collection:
        try:
            client.delete_collection(name=collection_name)
            print(f"🗑️ Deleted existing collection '{collection_name}' for clean rebuild.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Prepare batches
    print(f"🧠 Embedding and indexing with model '{EMBEDDING_MODEL_NAME}' in batches of {batch_size}...")
    
    ids = []
    documents = []
    metadatas = []
    seen_ids = set()

    for idx, chunk in enumerate(chunks):
        c_id = str(chunk.get("chunk_id", "")).strip()
        if not c_id or c_id in seen_ids:
            c_id = f"chunk_{idx:05d}_{chunk.get('document_name', 'doc')[:10]}"
        seen_ids.add(c_id)

        content = str(chunk.get("content", "")).strip()
        # If content is empty for visual chunk, use caption as searchable content
        if not content and chunk.get("caption"):
            content = f"Visual plate caption: {chunk.get('caption')}"
        if not content:
            content = f"Document passage from {chunk.get('document_name', 'archive')}"

        meta = sanitize_metadata(chunk)

        ids.append(c_id)
        documents.append(content)
        metadatas.append(meta)

    # Batch upsert with progress bar
    total_batches = (len(ids) + batch_size - 1) // batch_size
    for b in tqdm(range(total_batches), desc="Indexing Chunks into ChromaDB"):
        start = b * batch_size
        end = min(start + batch_size, len(ids))
        
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end]
        )

    indexed_count = collection.count()
    print(f"✅ SUCCESS: {indexed_count} chunks successfully indexed into ChromaDB collection '{collection_name}'!")
    print(f"💾 Vector store persisted to: {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    index_chunks()
