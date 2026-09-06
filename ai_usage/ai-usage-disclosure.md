# AI Usage Disclosure Form

> **Competition:** SLIIT Codefest 2026 AI Competition (Powered by IFS)
> **Team Name:** DeepThink
> **Sub-track:** 1A — Rich Answers, Not Just Text
> **Date:** August / September 2026

---

## 1. Overview of AI Tools Utilized

In compliance with **Section 4.1 (AI Usage Policy)** of the SLIIT Codefest 2026 Challenge Document, this document provides an honest, transparent account of all AI coding assistants, chat models, and generative tools used during the research, design, and development of this project.

| AI Tool / Model | Primary Purpose | Development Stage Used |
| :--- | :--- | :--- |
| **Claude 3.7 Sonnet / Google Antigravity** | Architectural brainstorming, drafting parser boilerplate, prompt refinement | Architecture Scaffolding, Ingestion, UI & Hardening |
| **Groq Cloud (`qwen/qwen3.8-27b`)** | Ultra-fast runtime LPU generation engine (300+ tokens/sec, ~1.35s latency) | Runtime Inference, Grounding & Evaluation |
| **HuggingFace (`BAAI/bge-small-en-v1.5`)** | 100% Free local dense embeddings for persistent ChromaDB vector retrieval | Vector Embedding & Persistent ChromaDB Indexing |

---

## 2. Human vs. AI Contributions & Decision Breakdown

### 2.1 Decisions Made Exclusively by the Human Team
1. **Sub-track Selection (1A):** The human team identified that enterprise value in the Ashen Era Archive lay in resolving schematics, plate diagrams, and tables rather than pure text summaries.
2. **Modality-Aware Chunking Architecture:** Conceiving the `chunks.json` contract and the separation of `text`, `table`, and `image-caption` chunks with direct file linking.
3. **Compound RAG 3.0 Formulation:** Designing agentic sub-query decomposition, character dossier boosts (+0.35), and multi-entity intersection boosts (+0.40) to resolve complex comparative queries.
4. **Dynamic 3-Stage Context Budgeting:** Implementing intent-based sizing ($K=2$ to $K=8$), relative score Elbow drop-off ($\alpha=0.60$), and token packing (2,500 tokens) to replace manual UI sliders.
5. **Strict Epistemic Restraint (Directive 5):** Auditing initial hallucinations and enforcing strict non-extrapolation rules (verbatim reporting of contradictory records with zero speculative bridging).
6. **Pre-Generation Verification Gate:** Designing the entity presence and field verification gate to refuse unrecorded entities before LLM invocation.
7. **100% Free Local-First Architecture:** Eliminating cloud embedding bottlenecks and credit-card dependencies by standardizing on `BAAI/bge-small-en-v1.5` running locally inside ChromaDB.

### 2.2 Tasks Accelerated by AI Assistance
1. **Syntax & Boilerplate Generation:** Writing standard PyMuPDF image extraction filters and Streamlit component layouts.
2. **Regex & Markdown Parsing:** Drafting regular expressions for citation matching, field normalization, and table string formatting.
3. **Documentation Scaffolding:** Structuring markdown templates and formatting markdown tables.

---

## 3. Human Validation & Quality Assurance Protocol

- **No Unvalidated Code:** Every script generated or suggested by an AI tool was reviewed, modified, and locally tested on real Ashen Era corpus files by the assigned module lead.
- **Defense Readiness:** Every team member has reviewed all 4 modules and is prepared to explain, defend, and live-code modifications before the judging panel during the final round.
- **Chat Logs Exported:** Raw plain-text exports of all development chat sessions with AI assistants are preserved in `ai_usage/claude.md` and related files.
