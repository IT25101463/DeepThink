# Architecture Decision Log (ADR)

This document records the key architectural and design decisions made throughout the SLIIT Codefest 2026 AI Competition. Maintaining this log satisfies the requirements for **Engineering Best Practices (15%)** and **Technical Judgment & Decisions (10%)**.

---

## ADR-001: Selection of Sub-track 1A (Rich Answers, Not Just Text)
- **Date:** 2026-08-29
- **Status:** Accepted
- **Context:** The competition offers three sub-tracks (1A: Rich Answers, 1B: Connecting Facts, 1C: Human-like Search). The Ashen Era Archive contains 415 documents, including 3 codex books full of figure plates and tables, plus scanned ephemera.
- **Decision:** Select **Sub-track 1A**.
- **Rationale:** A vast amount of critical domain information in technical documents and the Ashen Era Archive lives inside diagrams, schematic figure plates, and ledger tables. Building an assistant that directly retrieves and embeds these visual assets solves a severe limitation of current enterprise RAG bots.
- **Trade-offs / Consequences:** Requires extracting and storing bounding boxes/images from PDFs/scans and passing image paths dynamically to the generation and UI layers.

---

## ADR-002: LLM & Embedding Infrastructure (OpenRouter + Local BGE)
- **Date:** 2026-08-29
- **Status:** Superseded by ADR-008
- **Context:** Competition rules encourage frugal engineering and free/low-cost API usage with strict rate-limit protection.
- **Decision:** Use OpenRouter for generation and local embeddings for retrieval.

---

## ADR-003: Modality-Tagged Chunk Contract (`chunks.json`)
- **Date:** 2026-08-29
- **Status:** Accepted
- **Context:** Four team members need to work concurrently on ingestion, retrieval, generation, and UI without blocking one another.
- **Decision:** Define a strict JSON schema for chunks at Day 1 (`chunks.json`) containing `chunk_id`, `document_name`, `page_number`, `modality` (`text` | `table` | `image-caption`), `content`, `media_path`, and `metadata`.
- **Rationale:** Decouples ingestion (P1/P2) from retrieval indexing (P3) and generation prompting (P4). Members can mock `chunks.json` on Day 1 while parsers are developed.
- **Trade-offs / Consequences:** Ingestion must populate rich metadata for every extracted item.

---

## ADR-004: Local Vector Database Selection (ChromaDB)
- **Date:** 2026-08-29
- **Status:** Accepted
- **Context:** The solution must be easily reproducible by judges with a single command from the README. Cloud vector databases require account creation or network setup.
- **Decision:** Use **ChromaDB** in embedded/persistent local mode.
- **Rationale:** Zero external infrastructure dependencies; runs out of the box on judge machines; fast cosine similarity lookups with metadata filtering.
- **Trade-offs / Consequences:** Must ensure `.gitignore` excludes binary DB files while allowing automated build scripts to re-index cleanly.

---

## ADR-005: Inline Figure & Table Markdown Formatting Contract
- **Date:** 2026-08-29
- **Status:** Accepted
- **Context:** Generation engine needs to tell the Streamlit UI which image to display and where.
- **Decision:** Use standard Markdown image syntax `![Caption](path/to/image.png)` in the LLM response. Streamlit parses and renders these dynamically.
- **Rationale:** Compatible with both terminal/markdown viewers and web UI. No custom proprietary tags needed.
- **Trade-offs / Consequences:** Prompt must strictly instruct the LLM to only use verified paths provided in the retrieved context to avoid broken image links.

---

## ADR-006: Rebalancing Team Roles for Technical Execution & Rigorous Evaluation
- **Date:** 2026-08-31
- **Status:** Accepted
- **Context:** Competition rubrics allocate 25% to Technical Execution & Robustness, 15% to Problem Understanding, and 15% to Engineering Best Practices, while UI polish is explicitly stated as secondary. Having a dedicated full-time UI developer leaves the team under-resourced on heavy document extraction and evaluation.
- **Decision:** Rebalance the 4 roles:
  1. **P1:** Document Parsing & OCR Lead (Text, layout, degraded scan OCR).
  2. **P2:** Visual & Table Extraction Lead (Figure plates, maps, Markdown tables, media assets).
  3. **P3:** Retrieval & Reranking Lead (Embeddings, ChromaDB, intent routing, score boosting).
  4. **P4:** Generation, Evaluation & Delivery Lead (Grounded LLM, automated benchmark evaluation, lightweight Streamlit UI, demo video & report).
- **Rationale:** Distributes the difficult multimodal extraction workload evenly, introduces a dedicated owner for rigorous evaluation and hallucination elimination, and treats UI as a lightweight presentation layer.

---

## ADR-007: Accelerated Direct Multimodal Pipeline Implementation
- **Date:** 2026-08-31
- **Status:** Accepted
- **Context:** Building an artificial text-only system before multimodal extraction delays the core Sub-track 1A deliverable. The team can achieve higher quality by directly implementing the full multimodal ingestion, modality-aware retrieval, and grounded figure generation from Day 1.
- **Decision:** Consolidate development into a direct 3-phase execution roadmap: (1) Core Multimodal Engine Build, (2) Hardening, Rate-Limit Defense & Benchmark Evaluation, and (3) Video Production & Submission Packaging.
- **Rationale:** Delivers a fully working end-to-end prototype early, maximizing the remaining time available for rigorous adversarial testing, benchmark optimization, and video polish.

---

## ADR-008: 100% Free Local Embeddings with BAAI/bge-small-en-v1.5
- **Date:** 2026-09-01
- **Status:** Accepted
- **Context:** Cloud embedding APIs require credit card verification and introduce network latency and HTTP 429 rate limit risks during live evaluations and video recordings.
- **Decision:** Standardize vector embeddings on **`BAAI/bge-small-en-v1.5`** via HuggingFace `sentence-transformers` running locally inside ChromaDB.
- **Rationale:** 
  1. **Zero Cost & Zero Cards:** Requires zero payment cards, zero accounts, and zero external API keys.
  2. **Zero Rate Limits:** Embeddings compute locally on CPU/Apple Silicon with zero network dependencies.
  3. **State of the Art Quality:** BGE is top-ranked on the Massive Text Embedding Benchmark (MTEB) for retrieval precision.
  4. **Native ChromaDB Integration:** ChromaDB natively supports sentence-transformer embedding functions with 2 lines of code.
- **Trade-offs / Consequences:** Requires initial download of the lightweight model weights (~130MB) on first run.
