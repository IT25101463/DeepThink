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

## ADR-002: LLM & Embedding Infrastructure (Voyage AI + OpenRouter)
- **Date:** 2026-08-29
- **Status:** Accepted
- **Context:** Competition rules encourage frugal engineering and free/low-cost API usage with strict rate-limit protection.
- **Decision:** 
  - Embeddings: **Voyage AI (`voyage-4`)** using the 200M free token tier.
  - LLM Generation: **OpenRouter** utilizing free tier high-parameter models (e.g., `meta-llama/llama-3.3-70b-instruct:free`) with automated exponential backoff retry.
- **Rationale:** Voyage-4 provides frontier-grade semantic embeddings and shares the vector space across lite and large models. OpenRouter provides access to frontier open-weight models without vendor lock-in.
- **Trade-offs / Consequences:** Must implement robust HTTP 429 backoff handling (`tenacity` / retry loop) to withstand free-tier rate limits.

---

## ADR-003: Modality-Tagged Chunk Contract (`chunks.json`)
- **Date:** 2026-08-29
- **Status:** Accepted
- **Context:** Four team members need to work concurrently on ingestion, retrieval, generation, and UI without blocking one another.
- **Decision:** Define a strict JSON schema for chunks at Day 1 (`chunks.json`) containing `chunk_id`, `document_name`, `page_number`, `modality` (`text` | `table` | `image-caption`), `content`, `media_path`, and `metadata`.
- **Rationale:** Decouples ingestion (P1) from retrieval indexing (P2) and generation prompting (P3). P2, P3, and P4 can mock `chunks.json` on Day 1 while P1 builds parsers.
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
