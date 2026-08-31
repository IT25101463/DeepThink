# Member P2 Workflow: Visual & Table Extraction Lead

> **Owner:** Member P2  
> **Area of Responsibility:** Figure Plates & Diagram Extraction, Codex Table Extraction to Markdown, Media Asset Pipeline, Visual Metadata Enrichment  
> **Key Deliverables:** `src/ingestion/media_extractor.py`, `src/ingestion/table_extractor.py`, extracted assets in `data/extracted_media/`, and `image-caption`/`table` entries in `data/chunks.json`

---

## 1. Role Scope & Objectives

In **Sub-track 1A (Rich Answers, Not Just Text)**, extracting visual diagrams, figure plates, and complex structured tables is the core technical differentiator.

Member P2 is responsible for:
1. Extracting high-resolution figures, schematics, anatomical plates, maps, and faction crests from PDFs and image folders.
2. Parsing complex multi-column tables in codex data books into structured, cleanly formatted Markdown tables.
3. Cropping and saving media assets to `data/extracted_media/figures/` and `data/extracted_media/tables/`.
4. Generating `image-caption` and `table` chunks with rich captions, section context, and valid local file paths in `chunks.json`.

---

## 2. Complete Execution Checklist (Today)

### Stage 1: Figure Plate & Image Extraction
- [x] Implement `extract_images_from_pdf(pdf_path, output_dir)` in `src/ingestion/media_extractor.py` using `PyMuPDF` (`fitz`).
- [x] Filter out tiny decorative icons, page borders, and blank blocks ($\text{width} \ge 100\text{px}, \text{height} \ge 100\text{px}$).
- [x] Save images into `data/extracted_media/figures/<doc>_p<page>_fig<idx>.png`.
- [x] Extract nearby caption text and generate `image-caption` chunks.
- [x] Ingest standalone figure plates and wiki illustrations from corpus image archives.

### Stage 2: Structured Table Extraction
- [x] Implement `extract_tables_from_pdf(pdf_path)` in `src/ingestion/table_extractor.py` using `pdfplumber`.
- [x] Format extracted tables into clean Markdown tables with aligned header columns.
- [x] Generate `table` chunks with dimension and entity metadata.

### Stage 3: Verification & Integration
- [x] Ensure all `media_path` references exist on disk:
  ```python
  assert os.path.exists(chunk["media_path"])
  ```
- [x] Merge visual and table chunks with P1 text chunks into `data/chunks.json`.
- [x] Validate entire contract:
  ```bash
  python3 -m src.utils.schema_validator data/chunks.json
  ```
- [x] 24/24 unit tests passing in `tests/test_media_extractor.py`, `tests/test_table_extractor.py`, and test suite.

---

## 3. Data Contract Format

```json
{
  "chunk_id": "codex_v1_p14_fig02",
  "document_name": "Codex_Titanica_Vol_1.pdf",
  "document_type": "pdf",
  "page_number": 14,
  "section_title": "Sky-Fortress Pressure Assembly",
  "modality": "image-caption",
  "content": "Schematic of the primary steam coolant valve showing pressure gauge tolerances, safety bypass conduit, and manual override lever.",
  "media_path": "data/extracted_media/figures/codex_v1_p14_fig02.png",
  "caption": "Figure 14.2: Primary Steam Coolant Valve Assembly Schematic",
  "metadata": {
    "dimensions": [800, 600],
    "source_reliability": "official_codex",
    "related_entities": ["Coolant Valve", "Sky-Fortress", "Pressure Assembly"]
  }
}
```
