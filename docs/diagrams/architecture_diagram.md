# DeepThink — Architecture & Flow Diagrams

This document contains visual diagrams for DeepThink's multimodal ingestion, compound retrieval, and grounded generation architecture for **Sub-track 1A: Rich Answers, Not Just Text**.

---

## 1. End-to-End System Sequence Diagram (Compound RAG 3.0)

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User
    participant UI as 🖥️ P4: Streamlit UI
    participant Guard as 🛡️ P3: Domain Guardrail (router.py)
    participant Budget as ⚙️ P3: Adaptive Budgeter & Entity Matcher
    participant Agent as 🔄 P3: Agentic Decomposer
    participant VDB as 🗄️ P3: Local ChromaDB (BGE-small-en-v1.5)
    participant Rank as 🎯 P3: Cross-Encoder Re-Ranker
    participant Verif as ⚖️ P3: Pre-Gen Verifier (Elbow α=0.60)
    participant LLM as ⚡ P4: Groq Cloud LPU (openai/gpt-oss-120b)
    participant Media as 🖼️ P2: Media Store (data/extracted_media/)

    User->>UI: Submits Query (e.g. "Show diagram of Gauntlet of Sorrowfell")
    UI->>Guard: check_query_domain_scope(query)

    alt Out-of-Scope / Abuse / Sensor Premise
        Guard-->>UI: Fast-Path Categorized Refusal (< 0.005s, 0 tokens) + 3 Archival Options
        UI-->>User: Renders professional refusal with suggested topics
    else In-Scope Archival Query
        Guard->>Budget: extract_entities_and_fields() & size_context_budget()
        Budget-->>Agent: Dynamic Target K (K=2 for visual/facts, K=6..8 for matrices)
        Agent->>VDB: Query dense vectors across sub-queries (Local BGE-small)
        VDB-->>Agent: Multi-hop candidate chunks
        Agent->>Rank: Candidate pool with hop corroboration (+25%)
        Rank->>Rank: Compute composite cross-relevance (+0.35 Dossier, +0.40 Multi-Entity, 1.5x Modality)
        Rank->>Verif: Top-ranked candidate chunks
        Verif->>Verif: Elbow score drop-off (prune Score < 0.60 × TopScore) & Pack 2,500 tokens
        Verif-->>LLM: Verified context chunks with media paths & citations
        LLM->>LLM: Synthesize report (Directive 5 Epistemic Restraint, 300+ t/s)
        LLM-->>UI: Grounded Markdown with embedded ![Caption](media_path)
        UI->>Media: Resolve local media paths on disk
        UI-->>User: Displays rich answer with native figures, tables, and telemetry
    end
```

---

## 2. Ingestion & Extraction Pipeline Diagram (P1 & P2)

```mermaid
graph LR
    subgraph Corpus [The Ashen Era Archive (415 docs, 1,277 pages)]
        PDF[PDF Chronicles & Codexes]
        DOCX[DOCX Letters & Transcripts]
        MD[Fan-Wiki Articles]
        SCANS[Simulated Scans & Ephemera]
        STANDALONE[Standalone Plate Images]
    end

    subgraph P1 Lead [P1 Lead: Text Parsing & OCR]
        PDF --> PyMuPDF_Text[PyMuPDF Text Extractor]
        DOCX --> DocxParser[python-docx Parser]
        MD --> MDParser[Markdown Header Splitter]
        SCANS --> Tesseract[Tesseract OCR Engine]

        PyMuPDF_Text --> TxtChunk[Hierarchical Text Chunker ~800 chars]
        DocxParser --> TxtChunk
        MDParser --> TxtChunk
        Tesseract --> TxtChunk
    end

    subgraph P2 Lead [P2 Lead: Visual & Table Extraction]
        PDF --> PyMuPDF_Img[PyMuPDF Image Extractor]
        PDF --> Plumber_Tab[pdfplumber Table Extractor]
        STANDALONE --> ImgIngest[Standalone Plate Ingestion]

        PyMuPDF_Img --> FiguresDir[(data/extracted_media/figures/)]
        STANDALONE --> FiguresDir
        Plumber_Tab --> TablesDir[(data/extracted_media/tables/)]

        PyMuPDF_Img --> VisualChunk[Image-Caption Chunks]
        STANDALONE --> VisualChunk
        Plumber_Tab --> TableChunk[Markdown Table Chunks]
    end

    subgraph Output Contract [data/chunks.json Contract (9,312 Chunks)]
        TxtChunk --> MasterJSON[(data/chunks.json)]
        VisualChunk --> MasterJSON
        TableChunk --> MasterJSON
    end
```

---

## 3. Dynamic 3-Stage Adaptive Context Budgeting (P3)

```mermaid
graph TD
    Q[User Query] --> S1[Stage 1: Intent & Entity Sizing]
    S1 -->|"Single Fact / Visual Blueprint (1 entity)"| K2[Allocate Target K = 2]
    S1 -->|"Standard Lore Inquiry"| K4[Allocate Target K = 4]
    S1 -->|"Comparative Matrix / Multi-Hop (2+ entities)"| K8[Allocate Target K = 6 to 8]

    K2 & K4 & K8 --> S2[Stage 2: Cross-Encoder Re-Ranking]
    S2 --> ReRankScore[Composite Score with Dossier +0.35 & Multi-Entity +0.40 Bonuses]

    ReRankScore --> S3[Stage 3: Pre-Generation Verification & Pruning]
    S3 --> ElbowCheck{Elbow Cutoff: Score >= 0.60 × TopScore?}
    ElbowCheck -->|Yes| KeepChunk[Retain Candidate]
    ElbowCheck -->|No| DropChunk[Prune Trailing Noise Distractor]

    KeepChunk --> TokenPack[Token Density Packing: Cap at 2,500 Tokens]
    TokenPack --> ContextForLLM[High-Precision Context Chunks for Groq LPU]
```

---

## 4. Team Ownership & Component Architecture

| Member | Role | Core System Component | Deliverables |
| :--- | :--- | :--- | :--- |
| **Fatheen M. F. A.** | **P1 Lead** | Multi-Format Document Parsing & OCR | `src/ingestion/parser.py`, `src/ingestion/ocr_engine.py`, text chunks in `chunks.json` |
| **M. M. M. Shakeer** | **P2 Lead** | Visual Media & Table Extraction | `src/ingestion/media_extractor.py`, `src/ingestion/table_extractor.py`, 86+ plates in `data/extracted_media/` |
| **Rasheed A. A. A.** | **P3 Lead (Team Lead)** | Retrieval, Compound RAG 3.0 & Ranking | `src/retrieval/` (indexer, retriever, router, budgeter, agentic, reranker, verifier) |
| **S. Dharshan** | **P4 Lead** | Grounded Generation, Evaluation & UI | `src/generation/generator.py`, `src/evaluation/evaluator.py`, `src/ui/app.py`, demo video & report |
