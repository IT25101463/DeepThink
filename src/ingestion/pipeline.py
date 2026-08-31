"""
Ingestion Pipeline Coordinator (Owners: Member P1 & Member P2)
Iterates through data/Ashen_Era_Archive/, runs multi-format text parsing, OCR,
and media extraction, and produces the master data/chunks.json contract.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.config import CORPUS_DIR, CHUNKS_JSON_PATH, EXTRACTED_MEDIA_DIR, PROJECT_ROOT
from src.ingestion.parser import parse_document
from src.ingestion.media_extractor import extract_images_from_pdf
from src.ingestion.table_extractor import extract_tables_from_pdf
from src.utils.schema_validator import validate_chunk, validate_chunks_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingestion_pipeline")


def run_ingestion_pipeline(corpus_path: Path = CORPUS_DIR, output_path: Path = CHUNKS_JSON_PATH) -> List[Dict[str, Any]]:
    """
    Main entry point for corpus ingestion.
    Parses all archive files, runs OCR, extracts media/tables, and exports chunks.json.
    """
    logger.info(f"Starting ingestion on corpus: {corpus_path.resolve()}")
    if not corpus_path.exists():
        logger.error(f"Corpus directory not found: {corpus_path}")
        return []

    # Supported extensions for P1 parsing
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".markdown", ".txt"}
    
    all_files = [
        f for f in corpus_path.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    logger.info(f"Discovered {len(all_files)} document files in archive.")

    all_chunks: List[Dict[str, Any]] = []
    seen_ids = set()
    
    # Progress tracking
    processed_count = 0
    errors_count = 0

    for file_path in all_files:
        try:
            # 1. P1: Parse text & OCR
            doc_chunks = parse_document(file_path)
            
            # 2. P2: Extract visual figures & tables (if PDF)
            if file_path.suffix.lower() == ".pdf":
                try:
                    img_chunks = extract_images_from_pdf(file_path, EXTRACTED_MEDIA_DIR / "figures")
                    doc_chunks.extend(img_chunks)
                except Exception as e:
                    logger.debug(f"P2 image extraction not active or skipped for {file_path.name}: {e}")

                try:
                    table_chunks = extract_tables_from_pdf(file_path)
                    doc_chunks.extend(table_chunks)
                except Exception as e:
                    logger.debug(f"P2 table extraction not active or skipped for {file_path.name}: {e}")

            # Validate and register chunks
            for chunk in doc_chunks:
                chunk_id = chunk.get("chunk_id")
                # Ensure unique ID
                if chunk_id in seen_ids:
                    count = 1
                    new_id = f"{chunk_id}_dup{count}"
                    while new_id in seen_ids:
                        count += 1
                        new_id = f"{chunk_id}_dup{count}"
                    chunk["chunk_id"] = new_id
                    chunk_id = new_id
                    
                seen_ids.add(chunk_id)
                all_chunks.append(chunk)

            processed_count += 1
            if processed_count % 25 == 0 or processed_count == len(all_files):
                logger.info(f"Progress: {processed_count}/{len(all_files)} files processed ({len(all_chunks)} chunks generated)...")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            errors_count += 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    logger.info(f"Ingestion complete: Processed {processed_count} files ({errors_count} errors).")
    logger.info(f"Total chunks generated: {len(all_chunks)} -> saved to {output_path}")

    # Validate output schema
    is_valid, val_errors = validate_chunks_file(output_path)
    if is_valid:
        logger.info("✅ chunks.json successfully validated against contract schema.")
    else:
        logger.warning(f"⚠️ chunks.json has {len(val_errors)} validation warning(s): {val_errors[:5]}")

    return all_chunks


if __name__ == "__main__":
    run_ingestion_pipeline()
