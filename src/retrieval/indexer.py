"""
Vector Indexer Module (Owner: Member P3)
Embeds chunks from data/chunks.json using Voyage AI (voyage-4) and indexes into local ChromaDB.
"""

import json
from pathlib import Path
from src.config import CHUNKS_JSON_PATH, CHROMA_PERSIST_DIR, VOYAGE_API_KEY, EMBEDDING_MODEL_NAME


def index_chunks(chunks_file: Path = CHUNKS_JSON_PATH):
    """
    Reads chunks.json, generates Voyage embeddings in batches, and indexes into ChromaDB.
    """
    if not chunks_file.exists():
        print(f"Chunks file not found: {chunks_file}. Run ingestion pipeline first.")
        return

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Indexing {len(chunks)} chunks using model: {EMBEDDING_MODEL_NAME}...")
    # TODO (P3): Implement Voyage AI embedding batch call + ChromaDB persistence


if __name__ == "__main__":
    index_chunks()
