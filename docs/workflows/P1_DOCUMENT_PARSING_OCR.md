# Member P1 Workflow: Document Parsing & OCR Lead

> **Owner:** Member P1  
> **Area of Responsibility:** Multi-Format Text Ingestion, Document Layout Parsing, OCR on Scans/Ephemera, Section Hierarchy & Text Chunks  
> **Key Deliverables:** `src/ingestion/parser.py`, `src/ingestion/ocr_engine.py`, and base text entries in `data/chunks.json`

---

## 1. Role Scope & Objectives

The *Ashen Era Archive* contains 415 documents (~1,277 pages) spread across novels, wiki articles, codex manuals, and scanned in-world ephemera (letters, trial transcripts, ledgers).

Member P1 is responsible for:
1. Building multi-format parsers for PDF, DOCX, Markdown, and Plain Text files.
2. Implementing an OCR pipeline (Tesseract / EasyOCR) for simulated scan ephemera and handwritten notes.
3. Preserving document structure (chapter headers, sections, page numbers, document source metadata).
4. Performing hierarchical text chunking (~800 characters with ~150 character overlap) and tagging metadata (`source_reliability`, `document_type`, `page_number`).

---

## 2. Complete Execution Checklist (Today)

### Stage 1: Document Parsing & Layout Extraction
- [ ] Implement `parse_markdown_file(path)` in `src/ingestion/parser.py` (extracting sections by `#` headers).
- [ ] Implement `parse_docx_file(path)` via `python-docx` for letters, ledgers, and official documents.
- [ ] Implement `parse_pdf_text(path)` via `PyMuPDF` (`fitz`) tracking page numbers and headers.
- [ ] Implement hierarchical chunker: split text into ~800 character chunks with ~150 character overlap while retaining document header context.

### Stage 2: OCR Engine for Scanned Ephemera & Scans
- [ ] Implement `run_ocr_on_image(image_path)` in `src/ingestion/ocr_engine.py` using `pytesseract`.
- [ ] Add image contrast enhancement and binarization via `PIL.ImageEnhance` to clean noisy simulated scans.
- [ ] Extract text from scanned trial transcripts, court martials, and tavern ballads.
- [ ] Assign `source_reliability` metadata tags (`official_codex`, `wiki`, `novel`, `ephemera_tavern`, `ephemera_trial`).

### Stage 3: Validation & Output Delivery
- [ ] Combine text and OCR chunks into `data/chunks.json`.
- [ ] Validate schema compliance:
  ```bash
  python3 -m src.utils.schema_validator data/chunks.json
  ```
- [ ] Verify 100% corpus coverage across all 415 archive documents.

---

## 3. Module Interface Contract

```python
from typing import List, Dict, Any
from pathlib import Path

def parse_document(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses a single file (PDF/DOCX/MD/TXT/Scan) and returns structured text chunks.
    """
    ...
```
