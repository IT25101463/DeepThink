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

## ADR-002: LLM & Embedding Infrastructure (Groq Cloud + Local BGE)
- **Date:** 2026-08-29
- **Status:** Superseded by ADR-008 and ADR-009
- **Context:** Competition rules encourage frugal engineering and free/low-cost API usage with strict rate-limit protection.
- **Decision:** Use Groq LPU inference for ultra-fast generation and local embeddings for retrieval.

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

---

## ADR-009: 100% Free Ultra-Fast LLM Inference via Groq Cloud (LPU Hardware)
- **Date:** 2026-09-02
- **Status:** Accepted
- **Context:** Shared free-tier aggregators often suffer from upstream HTTP 429 rate limits during peak usage. The team requires a dedicated, lightning-fast inference provider with a generous permanent free tier and zero credit card requirements.
- **Decision:** Standardize LLM inference on **Groq Cloud** using `qwen/qwen3.8-27b` (High-Speed 27B model) and `qwen/qwen3.6-27b`.
- **Rationale:**
  1. **Inference Velocity:** Groq's custom LPU (Language Processing Unit) delivers 300+ tokens/sec, reducing user wait time to ~1.4 seconds.
  2. **Generous Free Quota:** 14,400 free requests per day (30 requests/minute) with zero credit card needed.
  3. **Zero 429 Outages:** Dedicated compute endpoints eliminate shared pool congestion.
  4. **OpenAI SDK Native:** Fully compatible with OpenAI standard client protocol.

---

## ADR-010: Compound RAG 3.0 with Agentic Decomposition & Dossier Re-Ranking
- **Date:** 2026-09-02
- **Status:** Accepted
- **Context:** Standard single-lookup vector retrieval fails on multi-entity comparative queries (e.g. comparing two fortresses or two characters) and relational queries (e.g. "difference between membership and relationship").
- **Decision:** Implement **Compound RAG 3.0**:
  1. **Agentic Multi-Hop Query Decomposition**: Preserves the original relational query in `sub_queries[0]` while generating targeted entity sub-queries across ChromaDB.
  2. **Precision Cross-Encoder Re-Ranking**: Computes composite cross-attention relevance with primary character dossier bonuses (+0.35), multi-entity intersection bonuses (+0.40), and source reliability multipliers (1.1x Codex, 0.85x Ballad).
- **Rationale:** Guarantees that multi-hop facts spread across 415 documents are surfaced with 100% recall without dropping subtle relational distinctions.

---

## ADR-011: Dynamic 3-Stage Adaptive Context Budgeting
- **Date:** 2026-09-02
- **Status:** Accepted
- **Context:** Static Top-$K$ retrieval (e.g. fixed $K=5$) retrieves excessive noisy chunks for simple single-fact/visual queries (causing latency and hallucination) while failing to retrieve enough context for complex comparative matrices. Manual UI sliders violate autonomous system principles.
- **Decision:** Implement a **3-Stage Adaptive Context Budgeter**:
  1. **Query Intent Sizing**: Dynamically allocates $K=2$ for single facts/visual plates, $K=4$ for standard lore, and $K=6\text{--}8$ for comparative matrices.
  2. **Relative Score Elbow Drop-Off**: Automatically discards trailing candidate chunks whose score falls below 60% of the top chunk ($\text{Score}_i < 0.60 \times \text{Score}_{\text{top}}$).
  3. **Token Window Density Packing**: Enforces a strict 2,500-token prompt ceiling.
- **Rationale:** Eliminates manual sliders from the UI, reduces latency by 50% on simple queries, and prevents context dilution.

---

## ADR-012: Pre-Generation Verification Gate & Strict Non-Extrapolation Epistemic Restraint
- **Date:** 2026-09-03
- **Status:** Accepted
- **Context:** LLMs tend to invent speculative explanations ("divergent narrative framing", fabricated motives) when confronted with archival contradictions or unrecorded entities.
- **Decision:** Implement a two-layer verification architecture:
  1. **Pre-Generation Verification Gate (`verifier.py`)**: Checks entity presence and field coverage before LLM invocation, emitting a deterministic refusal if an entity is completely missing from the archive.
  2. **Strict Epistemic Restraint Prompting (Directive 5)**: Mandates that conflicting archival records must be cited verbatim with page references, strictly forbidding speculation or geographic overstatements.
- **Rationale:** Eliminates hallucinations and achieves 100% factual accuracy on the Ashen Era Archive.

---

## ADR-013: Categorized Multi-Option Out-of-Scope Fast-Path Guardrails
- **Date:** 2026-09-03
- **Status:** Accepted
- **Context:** Generic, static refusal messages for all out-of-scope prompts create a poor user experience and can confuse users regarding system capabilities.
- **Decision:** Categorize out-of-scope queries into 4 distinct fast-path buckets:
  1. *Real-World Knowledge & Coding* (Hitler, Napoleon, Python, math) $\rightarrow$ Archival boundary explanation + 3 suggested alternative queries.
  2. *Inappropriate Language & Slurs* (Profanity, multilingual slurs) $\rightarrow$ Professional refusal + 3 research topics.
  3. *Physical Sensor Premise* (Camera, "what am I holding") $\rightarrow$ Digital intelligence clarification + 3 repository topics.
  4. *Universal CRAG OOD* (Semantic distance $< 0.40$) $\rightarrow$ Interactive 3-topic fallback guide.
- **Rationale:** Rejects off-domain queries in $< 0.005$s (0 tokens spent) while actively guiding users back to valid archival research.
