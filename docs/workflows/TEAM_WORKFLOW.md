# Team Master Execution Plan — Complete System Build

> **SLIIT Codefest 2026 AI Competition**  
> **Sub-track 1A:** *Rich Answers, Not Just Text*  
> **Corpus:** *The Ashen Era Archive* (415 documents, ~1,277 pages)  
> **Target:** Complete End-to-End Build, Benchmark Evaluation & Deliverables Preparation

---

## 1. Roles & Ownership

| Member | Role | Core Responsibility (Heavy Lifting) | Delivery / Secondary Focus |
| :--- | :--- | :--- | :--- |
| **P1** | **Document Parsing & OCR Lead** | Ingesting 415 corpus files (PDF/DOCX/MD/TXT), running OCR (Tesseract) on degraded simulated scans, section hierarchy, and text chunking. | Metadata enrichment (`source_reliability`, `document_type`, `page_number`). |
| **P2** | **Visual & Table Extraction Lead** | Extracting figure plates, diagrams, maps, cropping images, converting complex codex tables to Markdown, linking media assets. | Maintaining `image-caption` & `table` entries in `chunks.json`. |
| **P3** | **Retrieval & Reranking Lead (Team Leader)** | Voyage AI embeddings (`voyage-4`), ChromaDB indexing, query intent classifier, modality score boosting, and Voyage `rerank-2.5` reranking. | Hybrid search (Dense + BM25) and retrieval latency optimization. |
| **P4** | **Generation, Evaluation & Delivery Lead** | OpenRouter LLM grounding, hallucination guardrails, automated benchmark evaluation on `sample_questions.json`. | Streamlit UI integration, 10-min demo video, and 5-page submission report. |

---

## 2. Complete Execution Assembly Line

```mermaid
flowchart TD
    subgraph Stage 1 [Stage 1: Ingestion & Asset Pipeline]
        P1[P1: Multi-Format Parser & Scan OCR] --> ChunksContract[(data/chunks.json Contract)]
        P2[P2: Figure Plates & Table Extraction] --> ChunksContract
        P2 --> MediaStore[(data/extracted_media/)]
    end

    subgraph Stage 2 [Stage 2: Modality-Aware Retrieval & Vector DB]
        ChunksContract --> P3Index[P3: Voyage-4 Batch Embeddings & ChromaDB Indexer]
        UserQuery[User Question] --> IntentRouter[P3: Modality Intent Classifier]
        IntentRouter --> HybridSearch[P3: Modality-Aware Weighted Search]
        P3Index --> HybridSearch
        HybridSearch --> Rerank[P3: Voyage rerank-2.5 Top-5 Chunks]
    end

    subgraph Stage 3 [Stage 3: Grounded LLM & Interactive UI]
        Rerank --> LLMGen[P4: OpenRouter Grounded Synthesis & Image Injection]
        UserQuery --> LLMGen
        LLMGen --> StreamlitApp[P4: Streamlit Interactive Assistant]
        MediaStore --> StreamlitApp
    end

    subgraph Stage 4 [Stage 4: Automated Benchmark & Deliverables]
        StreamlitApp --> Benchmark[P4: Automated Evaluation Suite on sample_questions.json]
        Benchmark --> MetricsDoc[docs/metrics.md Precision/Citation/Hallucination Log]
        MetricsDoc --> VideoScript[10-Minute Demo Video Recording Script]
        MetricsDoc --> FinalReport[5-Page PDF Submission Report]
    end
```

---

## 3. Execution Checklist

- [x] **Setup & Scaffolding:** Repository layout, `.gitignore`, `.env.example`, `requirements.txt`, unit test suite (`6/6 OK`).
- [ ] **Stage 1 (Ingestion & Extraction):** Build `src/ingestion/parser.py`, `ocr_engine.py`, `media_extractor.py`, and `table_extractor.py`.
- [ ] **Stage 2 (Retrieval & Indexing):** Build `src/retrieval/indexer.py`, `router.py`, and `retriever.py` with Voyage AI embeddings and modality boosting.
- [ ] **Stage 3 (Generation & UI):** Build `src/generation/generator.py` and `src/ui/app.py` with citation enforcement and inline media rendering.
- [ ] **Stage 4 (Evaluation & Hardening):** Build `src/evaluation/evaluator.py`, execute the 20-question benchmark, and log verified metrics in `docs/metrics.md`.
- [ ] **Stage 5 (Deliverables):** Prepare 10-minute demo video script outline and 5-page submission report structure.
