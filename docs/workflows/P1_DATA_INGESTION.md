# Member P1 Workflow: Data & Ingestion Lead

> **Owner:** Member P1  
> **Area of Responsibility:** Multi-Format Ingestion, OCR Extraction, Chunking, Media Linking, Metadata Enrichment & Data Contract Maintenance  
> **Key Deliverable:** High-quality `data/chunks.json` & extracted assets in `data/extracted_media/`

---

## 1. Role Scope & Objectives

The Ashen Era Archive consists of 415 documents (~1,277 pages) spanning 4 novels, ~90 wiki articles, 3 codex books, and ~150 ephemera documents (scans, ledgers, letters). 

Member P1 is responsible for:
1. Converting all raw files (PDF, DOCX, Markdown, Text, Scans) into clean, structured data chunks.
2. Extracting visual figure plates, illustrations, diagrams, and tables into standalone media files.
3. Generating the standardized `chunks.json` contract consumed by P2 (Retrieval) and P3 (Generation).
4. Ensuring metadata fidelity (document name, page number, section header, reliability type).

---

## 2. Shared Data Contract (`chunks.json` Schema)

P1 must output chunks strictly adhering to the agreed JSON schema:

```json
[
  {
    "chunk_id": "string (e.g. codex_vol1_p14_img01)",
    "document_name": "string (e.g. Codex_Titanica_Vol_1.pdf)",
    "document_type": "pdf | docx | md | txt | scan",
    "page_number": 14,
    "section_title": "string (e.g. Siege Automaton Schematic)",
    "modality": "text | table | image-caption",
    "content": "string (the narrative text, markdown table, or image caption/OCR text)",
    "media_path": "string or null (e.g. data/extracted_media/figures/codex_vol1_p14_img01.png)",
    "caption": "string or null",
    "metadata": {
      "word_count": 45,
      "source_reliability": "official_codex | novel | wiki | ephemera_tavern | ephemera_trial",
      "related_entities": ["Siege Engine", "Steam Core"]
    }
  }
]
```

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — Alignment & Corpus Audit
- [ ] Inspect raw files in `data/ashen_era_archive/`. Count files per extension.
- [ ] Establish directory structure: `data/raw/`, `data/extracted_media/`, `data/processed/`.
- [ ] Confirm and validate `chunks.json` schema with P2, P3, and P4.
- [ ] Prepare test sample of 10 diverse documents (1 PDF codex, 1 novel chapter, 2 wiki MDs, 2 scanned ephemera).

### Sprint 1 (Days 2–4) — Baseline Text Ingestion
- [ ] Build parsing script for text files, markdown articles, and text-based PDFs.
- [ ] Implement hierarchical chunking (chunk size: ~800 tokens, overlap: ~150 tokens) preserving section headers.
- [ ] Export baseline text-only `chunks.json` to unblock P2 (Retrieval) and P3 (Generation).
- [ ] Record text parsing failure cases.

### Sprint 2 (Days 5–9) — Core Multimodal Extraction (Sub-track 1A Engine)
- [ ] Implement image extraction using `PyMuPDF` (`fitz`) / `pdfplumber` for PDF codex books and figure plates.
- [ ] Save extracted images into `data/extracted_media/figures/` and `data/extracted_media/plates/`.
- [ ] Implement table extraction to convert complex ledger and stat tables into clean Markdown tables.
- [ ] Integrate lightweight OCR (Tesseract / EasyOCR) for simulated scan ephemera.
- [ ] Associate extracted images with nearby caption and section text in `image-caption` chunks.
- [ ] Generate complete multimodal `chunks.json` with all 415 documents.

### Sprint 3 (Days 10–11) — Ingestion Hardening & Error Analysis
- [ ] Run automated audit script to verify zero orphaned media links (`assert os.path.exists(chunk['media_path'])`).
- [ ] Clean noisy OCR text from degraded scans.
- [ ] Inspect and fix merged columns in codex tables.
- [ ] Benchmark parsing coverage across all 1,277 pages.

### Sprint 4 (Days 12–13) — Documentation & Report Contribution
- [ ] Write the **Data Ingestion & Multimodal Extraction** section of the 5-page submission report.
- [ ] Export AI prompt interaction logs to `ai_usage/claude.md`.
- [ ] Provide dataset statistics (total chunks, chunks per modality) for `docs/metrics.md`.

### Sprint 5 (Day 14) — Final Review & Defense Prep
- [ ] Rehearse verbal explanation of the ingestion pipeline and OCR trade-offs for judging Q&A.
- [ ] Ensure all ingestion scripts run reproducibly from `src/ingestion/pipeline.py`.

---

## 4. Input / Output Checklist

| Stage | Input | Expected Output | Verification Method |
| :--- | :--- | :--- | :--- |
| **Ingestion** | `data/ashen_era_archive/` (415 files) | `data/chunks.json` + `data/extracted_media/` | `python -m src.ingestion.validate` |
| **Verification** | `data/chunks.json` | 0 null fields, valid media paths, $>1000$ chunks | JSON Schema validation |
