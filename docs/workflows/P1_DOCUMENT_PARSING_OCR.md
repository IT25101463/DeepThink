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

## 2. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — Corpus Audit & Environment Setup
- [ ] Inspect raw files in `data/ashen_era_archive/`. Count files per extension.
- [ ] Set up parser dependencies (`pymupdf`, `python-docx`, `pytesseract`, `Pillow`).
- [ ] Validate the shared `chunks.json` schema contract with P2, P3, and P4.
- [ ] Test OCR on 3 sample scanned ephemera pages.

### Sprint 1 (Days 2–4) — Text Parsing & Baseline Chunks
- [ ] Implement text extraction for Markdown wiki articles and DOCX files.
- [ ] Implement PDF text extraction preserving page boundaries.
- [ ] Build hierarchical chunker: split text by headers and paragraphs, retaining document context headers.
- [ ] Output baseline text-only `chunks.json` to unblock P3 (Retrieval) and P4 (Generation/UI).
- [ ] Log parsing coverage and identify problematic/degraded scan files.

### Sprint 2 (Days 5–9) — OCR Pipeline for Scanned Ephemera
- [ ] Build dedicated OCR processor (`src/ingestion/ocr_engine.py`) for image-based PDFs and simulated scans.
- [ ] Apply preprocessing filters (contrast adjustment, binarization) to improve OCR accuracy on noisy scans.
- [ ] Extract and chunk trial transcripts, tavern notes, and ledger narratives.
- [ ] Tag metadata: assign `source_reliability` (`official_codex`, `wiki`, `novel`, `ephemera_tavern`, `ephemera_trial`).
- [ ] Merge OCR text chunks into the main `data/chunks.json`.

### Sprint 3 (Days 10–11) — Hardening & Edge Cases
- [ ] Run stress tests on edge cases: degraded scans, multi-page transcripts, footnotes.
- [ ] Clean OCR noise and token artifacts.
- [ ] Verify 100% corpus file coverage (all 415 documents parsed without crashes).

### Sprint 4 (Days 12–13) — Report Contribution & Code Cleanup
- [ ] Write the **Document Parsing, Structure Preservation & OCR** section for the 5-page submission report.
- [ ] Export AI prompt interaction logs to `ai_usage/claude.md`.
- [ ] Provide dataset metrics (total words parsed, OCR accuracy notes) for `docs/metrics.md`.

### Sprint 5 (Day 14) — Defense Preparation
- [ ] Rehearse explaining parsing trade-offs, OCR challenges, and text chunking strategy to judges.

---

## 3. Module Interface & Contract

```python
from typing import List, Dict, Any

def parse_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a single file (PDF/DOCX/MD/TXT/Scan) and returns structured text chunks.
    """
    ...
```
