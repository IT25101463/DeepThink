# Member P4 Workflow: Generation, Evaluation & Delivery Lead

> **Owner:** Member P4  
> **Area of Responsibility:** OpenRouter LLM Grounding & Citations, Automated Benchmark Evaluation Suite, Streamlit Web Interface, Demo Video Production & 5-Page Submission Report  
> **Key Deliverables:** `src/generation/generator.py`, `src/evaluation/evaluator.py`, `src/ui/app.py`, 10-Minute YouTube Demo Video, 5-Page `submission_report.pdf`

---

## 1. Role Scope & Objectives

Member P4 turns retrieved multimodal context into clear, grounded answers, runs benchmark testing, and delivers the user interface:
1. **Grounded Generation & Citation Enforcement:** Ensuring the LLM embeds relevant figures/tables (`![Caption](media_path)`) and strictly cites `[Document Name, Page Number]` with zero hallucinations.
2. **Automated Evaluation & Benchmarking:** Authoring and running automated evaluation test suites across the 20 sample questions to prove measurable before/after improvement.
3. **Streamlit UI Integration:** Connecting Ingestion (P1/P2), Retrieval (P3), and Generation (P4) into a clean, working web interface.
4. **Final Deliverables:** Recording the 10-minute demo video and compiling the 5-page submission report.

---

## 2. Complete Execution Checklist (Today)

### Stage 1: Grounded Generator (`src/generation/generator.py`)
- [ ] Connect OpenAI client configured for OpenRouter (`https://openrouter.ai/api/v1`).
- [ ] Use `meta-llama/llama-3.3-70b-instruct:free` (or `deepseek/deepseek-chat`).
- [ ] Implement exponential backoff retry via `tenacity` for HTTP 429 rate limit survival.
- [ ] Format prompt context with source metadata (`[Doc, Page]`) and media paths.
- [ ] Post-process output: verify all embedded markdown images `![Caption](path)` exist on disk before sending to UI.

### Stage 2: Streamlit Interactive UI (`src/ui/app.py`)
- [ ] Build chat interface with `st.chat_input` and message session state.
- [ ] Render generated responses with inline image plates and tables.
- [ ] Add expandable sidebar inspector to view retrieved chunk metadata, similarity scores, and reliability tags.

### Stage 3: Automated Benchmark & Evaluation (`src/evaluation/evaluator.py`)
- [ ] Loop through `data/sample_questions.json`.
- [ ] Run full pipeline (Retrieval $\rightarrow$ Generation).
- [ ] Compute metrics: Retrieval Precision, Citation Accuracy, Hallucination Rate, and Modality Success Rate.
- [ ] Record results table in `docs/metrics.md`.

---

## 3. Grounded System Prompt Specification

```text
SYSTEM PROMPT:
You are DeepThink, an expert enterprise document assistant for the Ashen Era Archive.
You answer user questions using ONLY the retrieved context chunks provided below.

RULES:
1. STRICT GROUNDING: Rely exclusively on facts in the retrieved context.
   If information is absent or unverified, state: "The archive records do not specify [detail]."
2. PRECISE CITATIONS: Cite the exact document and page number for every claim using:
   [Document Name, Page X].
3. INLINE FIGURE & TABLE EMBEDDING (CRITICAL):
   When context contains a chunk with modality 'image-caption' or 'table' and a valid media_path,
   you MUST embed the figure directly in your markdown answer:
   ![Figure Caption](media_path)
   Place the image directly adjacent to the relevant explanatory text.
4. SOURCE CONFLICT RESOLUTION:
   Highlight discrepancies between official codex records and ephemera/tavern songs.
```
