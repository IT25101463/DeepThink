"""
Ingestion Pipeline Coordinator (Owners: Member P1 & Member P2)
Iterates through data/ashen_era_archive/, runs text parsing, OCR, and media extraction,
and produces the master data/chunks.json contract.
"""

import json
from pathlib import Path
from src.config import CORPUS_DIR, CHUNKS_JSON_PATH, EXTRACTED_MEDIA_DIR


def run_ingestion_pipeline():
    """
    Main entry point for corpus ingestion.
    """
    print(f"Starting ingestion on corpus: {CORPUS_DIR}")
    chunks = []
    
    # 1. TODO: Parse text & OCR (P1)
    # 2. TODO: Extract images & tables (P2)
    # 3. Save chunks.json
    
    CHUNKS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
        
    print(f"Ingestion complete. {len(chunks)} chunks saved to {CHUNKS_JSON_PATH}")


if __name__ == "__main__":
    run_ingestion_pipeline()
