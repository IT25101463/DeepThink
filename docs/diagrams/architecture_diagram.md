# DeepThink — Architecture & Flow Diagrams

This document contains visual diagrams for DeepThink's multimodal ingestion, retrieval, and generation architecture.

---

## 1. End-to-End System Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as P4: Streamlit UI
    participant Gen as P3: Generation Engine
    participant Ret as P2: Modality-Aware Retriever
    participant VDB as P2: ChromaDB (Voyage-4)
    participant LLM as P3: OpenRouter LLM
    participant Media as P1: Media Store (Extracted)

    User->>UI: Enters Query (e.g. "Show me the Sky Fortress engine and explain its fuel valve")
    UI->>Gen: query_pipeline(query)
    Gen->>Ret: retrieve(query, top_k=5)
    
    Ret->>Ret: Classify Intent (Visual / Tabular / Narrative)
    Ret->>VDB: Query Vector Search (Voyage-4 Embeddings)
    VDB-->>Ret: Raw Vector Top-K
    Ret->>Ret: Apply Modality Weighting (Boost image-caption chunks)
    Ret-->>Gen: Filtered & Ranked Chunks with Media URIs

    Gen->>Gen: Build Grounded Prompt (Context + Image Markdown format)
    Gen->>LLM: Send Structured Prompt with Backoff Retry
    LLM-->>Gen: Generated Response (Explanation + ![Caption](media_path) + Citations)
    Gen->>Gen: Validate Media Paths against filesystem
    Gen-->>UI: Final Renderable Markdown
    
    UI->>Media: Resolve local media paths
    UI-->>User: Renders rich answer with embedded figures and source citations
```

---

## 2. Ingestion & Chunking Pipeline Diagram

```mermaid
graph LR
    subgraph Raw Documents
        PDF[PDFs & Codexes]
        DOCX[DOCX Files]
        MD[Wiki Markdown]
        SCANS[Simulated Scans]
    end

    subgraph P1 Ingestion Processing
        PDF --> PyMuPDF[PyMuPDF / pdfplumber]
        SCANS --> Tesseract[Tesseract OCR]
        DOCX --> DocxParser[python-docx]
        MD --> MDParser[Markdown Parser]
        
        PyMuPDF --> ImgExtract[Extract Figures & Plates]
        PyMuPDF --> TabExtract[Extract Structured Tables]
        PyMuPDF --> TxtExtract[Hierarchical Text Chunker]
        
        DocxParser --> TxtExtract
        MDParser --> TxtExtract
        Tesseract --> TxtExtract
    end

    subgraph Output Artifacts
        ImgExtract --> ExtractedFolder[(data/extracted_media/)]
        TabExtract --> ExtractedFolder
        TxtExtract --> ChunksJSON[(data/chunks.json)]
        ImgExtract --> ChunksJSON
        TabExtract --> ChunksJSON
    end
```

---

## 3. Modality-Aware Intent Routing

```mermaid
graph TD
    Q[User Query] --> C{Intent Classifier}
    C -->|"Visual / Schematic / Diagram"| V[Boost image-caption chunks x1.6]
    C -->|"Statistics / Tables / Metrics"| T[Boost table chunks x1.4]
    C -->|"Lore / Narrative / History"| N[Standard Dense Cosine Similarity]
    
    V --> Fusion[Rank Fusion & Deduplication]
    T --> Fusion
    N --> Fusion
    Fusion --> Out[Top-K Context Chunks for LLM]
```
