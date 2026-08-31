"""
Ingestion Package: Document parsing, OCR extraction, media extraction, and chunk generation.
Owners: Member P1 (Text/OCR) & Member P2 (Visual/Tables)
"""

from src.ingestion.parser import (
    parse_document,
    parse_markdown_file,
    parse_docx_file,
    parse_pdf_text,
    parse_txt_file,
    hierarchical_chunk,
    assign_source_reliability,
    detect_document_type,
)
from src.ingestion.ocr_engine import (
    run_ocr_on_image,
    preprocess_image_for_ocr,
    process_scanned_pdf,
    is_scanned_page,
)

__all__ = [
    "parse_document",
    "parse_markdown_file",
    "parse_docx_file",
    "parse_pdf_text",
    "parse_txt_file",
    "hierarchical_chunk",
    "assign_source_reliability",
    "detect_document_type",
    "run_ocr_on_image",
    "preprocess_image_for_ocr",
    "process_scanned_pdf",
    "is_scanned_page",
]
