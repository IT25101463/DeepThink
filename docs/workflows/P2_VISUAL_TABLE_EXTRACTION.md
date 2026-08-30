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

## 2. Shared Data Contract (`image-caption` and `table` Chunks)

```json
{
  "chunk_id": "codex_v1_p14_fig02",
  "document_name": "Codex_Titanica_Vol_1.pdf",
  "document_type": "pdf",
  "page_number": 14,
  "section_title": "Sky-Fortress Pressure Assembly",
  "modality": "image-caption",
  "content": "Schematic of the primary steam coolant valve showing pressure gauge tolerances and safety bypass.",
  "media_path": "data/extracted_media/figures/codex_v1_p14_fig02.png",
  "caption": "Figure 14.2: Coolant Valve Assembly Schematic",
  "metadata": {
    "dimensions": [800, 600],
    "source_reliability": "official_codex",
    "related_entities": ["Coolant Valve", "Sky-Fortress", "Pressure Assembly"]
  }
}
```

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — Media Schema & Tooling Setup
- [ ] Inspect codex PDFs and ephemera for image formats, plates, and table layouts.
- [ ] Set up extraction tools (`PyMuPDF` / `fitz`, `pdfplumber`, `Pillow`).
- [ ] Create directory structure: `data/extracted_media/figures/`, `data/extracted_media/tables/`.
- [ ] Validate schema with P1, P3, and P4.

### Sprint 1 (Days 2–4) — Extraction Prototyping
- [ ] Build script to extract raw images from PDF pages using PyMuPDF.
- [ ] Filter out tiny decorative icons, page borders, and blank blocks (set minimum width/height thresholds $\ge 100\text{px}$).
- [ ] Prototype table extraction using `pdfplumber` / markdown serializer.
- [ ] Provide sample media chunks to P3 and P4 to verify end-to-end rendering flow.

### Sprint 2 (Days 5–9) — Complete Multimodal Asset Pipeline (Sub-track 1A Engine)
- [ ] Process all 3 codex books full of tables and figure plates.
- [ ] Extract in-world ephemera images (maps, faction emblems, letter seals).
- [ ] Associate each image with surrounding caption text and section context to produce rich `image-caption` chunks.
- [ ] Convert all complex codex tables into clean Markdown tables (preserving header alignment).
- [ ] Save all extracted media assets with deterministic naming (`<doc>_p<page>_<type><index>.png`).
- [ ] Merge visual and table chunks into `data/chunks.json`.

### Sprint 3 (Days 10–11) — Quality Audit & Gap Resolution
- [ ] Verify zero broken links: run verification script asserting `os.path.exists(chunk['media_path'])` for all chunks.
- [ ] Inspect extracted tables to ensure no merged cells or misaligned columns corrupted numerical data.
- [ ] Benchmark visual retrieval coverage on figure questions in `sample_questions.json`.

### Sprint 4 (Days 12–13) — Report Contribution
- [ ] Write the **Visual Asset Extraction, Table Structuring & Multimodal Pipeline** section of the 5-page report.
- [ ] Include sample figures, extraction architecture, and before/after table extraction examples.
- [ ] Export AI prompt interaction logs to `ai_usage/claude.md`.

### Sprint 5 (Day 14) — Defense Preparation
- [ ] Prepare live explanation and demonstration of the extraction and image linking pipeline for judging Q&A.

---

## 4. Module Interface & Contract

```python
from typing import List, Dict, Any

def extract_media_from_pdf(pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Extracts figure plates, images, and tables from a PDF file, saves images to disk,
    and returns a list of modality-tagged chunks.
    """
    ...
```
