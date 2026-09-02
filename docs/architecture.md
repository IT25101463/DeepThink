# DeepThink — System Architecture Specification

> **SLIIT Codefest 2026 AI Competition**  
> **Sub-track 1A:** *Rich Answers, Not Just Text*  
> **Target Corpus:** *The Ashen Era Archive* (415 docs, ~1,277 pages)  
> **100% Free & Local-First Architecture**

---

## 1. High-Level Architecture Overview

DeepThink is designed to bridge the gap between unstructured multi-format enterprise documents and end-user visual comprehension. Instead of collapsing all documents into flat text, DeepThink preserves layout, tables, diagrams, and figures as distinct first-class entities with bidirectional links to their narrative context.

```mermaid
flowchart TD
    subgraph Ingestion Layer [P1 & P2: Ingestion & Extraction]
        Corpus[Ashen Era Archive<br/>PDF, DOCX, MD, TXT, Scans] --> Parser[P1: Multi-Format File Parser]
        Corpus --> OCR[P1: Tesseract OCR for Scans]
        Corpus --> ExtImg[P2: Figure & Image Extractor]
        Corpus --> ExtTab[P2: Table to Markdown Extractor]
        Parser --> TextChunk[P1: Hierarchical Text Chunking]
        ExtImg --> ChunksContract[(chunks.json Contract)]
        ExtTab --> ChunksContract
        TextChunk --> ChunksContract
        OCR --> ChunksContract
        ExtImg --> MediaStore[(data/extracted_media/)]
        ExtTab --> MediaStore
    end

    subgraph Retrieval Layer [P3: Local Vector Indexing & Modality-Aware Retrieval]
        ChunksContract --> LocalEmbed[Local BAAI/bge-small-en-v1.5 Embedding]
        LocalEmbed --> ChromaIndex[(ChromaDB Vector Store)]
        UserQuery[User Question] --> IntentClassifier[Query Intent Classifier]
        IntentClassifier --> HybridSearch[Modality-Aware Hybrid Retriever]
        ChromaIndex --> HybridSearch
        HybridSearch --> RankedChunks[Top-K Modality-Weighted Chunks]
    end

    subgraph Generation & Evaluation Layer [P4: Synthesis & Grounding]
        RankedChunks --> PromptBuilder[Context & Citation Assembler]
        UserQuery --> PromptBuilder
        PromptBuilder --> GroqLLM[Groq LPU LLM Engine<br/>Llama-3.3 70B @ 300 t/s]
        GroqLLM --> HallucinationGuard[Grounding & Citation Validator]
        HallucinationGuard --> FormattedOutput[Markdown Answer + Inline Media Links]
        FormattedOutput --> Evaluator[Automated Evaluation Suite<br/>src/evaluation/]
    end

    subgraph Interface Layer [P4: Interactive Visualization UI]
        FormattedOutput --> StreamlitApp[Streamlit Web Application]
        MediaStore --> StreamlitApp
        StreamlitApp --> EndUser[Interactive User Experience]
    end
```

---

## 2. Core Data Contract: `chunks.json`

The shared contract uniting Ingestion (P1/P2), Retrieval (P3), Generation, and Evaluation (P4) is the standardized `chunks.json` schema.

```json
[
  {
    "chunk_id": "codex_v1_p42_tab01",
    "document_name": "Codex_Imperial_Vol_1.pdf",
    "document_type": "pdf",
    "page_number": 42,
    "section_title": "Artillery Calibers and Supply Logistics",
    "modality": "table", 
    "content": "| Caliber | Range (km) | Shell Type | Rate of Fire |\n|---|---|---|---|\n| 105mm | 15.2 | High Explosive | 6 rpm |\n| 155mm | 24.7 | Armor Piercing | 3 rpm |",
    "media_path": "data/extracted_media/tables/codex_v1_p42_tab01.png",
    "caption": "Imperial Artillery Specifications Table, Page 42",
    "metadata": {
      "word_count": 35,
      "source_reliability": "official_codex",
      "related_entities": ["Imperial Artillery", "105mm", "155mm"]
    }
  }
]
```

### Modality Definitions:
- `text`: Narrative paragraphs, wiki entries, dialogue, letters, transcripts.
- `table`: Structured data tables serialized as markdown text and optionally backed by an image render.
- `image-caption`: Visual plates, anatomical drawings, faction crests, map scans, and technical schematics, containing image caption text + OCR text + disk path to the image file.

---

## 3. Sub-track 1A: Modality-Aware Retrieval Strategy

Standard semantic search models match query terms against nearest text tokens. When a user asks:
> *"Show me the diagram of the Sky-Fortress engine layout and explain how the coolant valve works."*

A naive RAG pipeline retrieves paragraphs describing the Sky-Fortress, completely ignoring the schematic diagram on plate 14.

### DeepThink Modality-Aware Solution:
1. **Query Intent Detection:** A lightweight classifier parses whether the question asks for visual figures (`"diagram"`, `"figure"`, `"plate"`, `"map"`, `"show"`, `"look like"`) or structured data (`"table"`, `"specifications"`, `"stats"`, `"cost"`, `"dimensions"`).
2. **Dynamic Modality Weighting:**
   $$\text{FinalScore}(c) = \text{CosineSimilarity}(q, c) \times \mathbf{W}_{\text{modality}}(q, c)$$
   Where $\mathbf{W}$ boosts image and table chunks when visual intent is detected.
3. **Local Vector Search:** Fast, zero-rate-limit local embedding computation using `BAAI/bge-small-en-v1.5`.
4. **Parent Document Context Injection:** When a figure chunk is retrieved, the immediate surrounding text chunk (caption/explanation) is bundled with it.

---

## 4. Grounded Generation & Inline Visual Injection

The LLM is prompted with strict grounding rules:
- Every claim must cite `[Document Name, Page Number]`.
- When an image or table chunk is provided in context, the LLM must embed the media using markdown syntax:
  ```markdown
  ![Figure: Sky-Fortress Coolant Assembly](data/extracted_media/figures/sky_fortress_coolant_plate14.png)
  ```
- If the archive contains conflicting accounts (e.g. Tavern Ballad vs Official Codex), the LLM explicitly mentions the discrepancy rather than hallucinating a resolution.

---

## 5. Directory Mapping & Modules

- `src/ingestion/`: P1 (Text/OCR) and P2 (Visual/Table) modules for PDF/DOCX parsing, OCR, and figure extraction.
- `src/retrieval/`: P3 modules for Local BGE embeddings, ChromaDB, and intent routing.
- `src/generation/`: P4 modules for OpenRouter LLM calling, prompt formatting, and retry logic.
- `src/evaluation/`: P4 modules for automated metric evaluation against the 20 sample questions.
- `src/ui/`: P4 modules for Streamlit chat interface and media rendering.
