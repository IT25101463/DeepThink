# Member P3 Workflow: Generation Lead

> **Owner:** Member P3  
> **Area of Responsibility:** OpenRouter LLM Integration, Grounded Prompt Engineering, Citation Enforcement, Inline Visual Figure Markdown Injection & Rate-Limit Resilience  
> **Key Deliverable:** `src/generation/` module exposing `generate_answer(query, context_chunks)`

---

## 1. Role Scope & Objectives

In Sub-track 1A, the Generation Lead is responsible for turning retrieved multimodal context into clear, authoritative, and grounded responses.

Member P3 must ensure:
1. **Zero Hallucination:** The LLM only states facts verified by the retrieved context.
2. **Explicit Citations:** Every assertion carries a citation: `[Source: <Document>, Page: <P>]`.
3. **Inline Rich Media Embedding:** When image or table chunks are provided, the LLM includes direct Markdown images: `![Caption](media_path)` seamlessly within the prose.
4. **API Resilience:** Frugal, rate-limit-safe OpenRouter calls with automated exponential backoff retry.

---

## 2. Prompt Engineering Specification

```text
SYSTEM PROMPT:
You are DeepThink, an expert enterprise document assistant for the Ashen Era Archive.
You answer user questions using ONLY the retrieved context chunks provided below.

RULES:
1. GROUNDING: Do NOT invent, assume, or extrapolate facts outside the context.
   If information is not present or cannot be confirmed, explicitly state:
   "The available archive records do not specify [detail]."
2. CITATIONS: Cite the exact document and page number for every claim using:
   [Document Name, Page X].
3. RICH MODALITY (CRITICAL):
   If a retrieved chunk has modality 'image-caption' or 'table' with a valid media_path,
   you MUST embed the figure directly in your response using markdown:
   ![Figure Caption](media_path)
   Place the image directly adjacent to the relevant explanatory text.
4. SOURCE CONFLICTS:
   If an official codex and an ephemera/tavern account contradict, explicitly highlight both perspectives.
```

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — OpenRouter Setup & Free Tier Verification
- [ ] Create OpenRouter account (openrouter.ai) and generate API key.
- [ ] Test calling free models (`meta-llama/llama-3.3-70b-instruct:free`, `qwen/qwen-2.5-72b-instruct:free`).
- [ ] Implement exponential backoff retry wrapper (`tenacity` or custom backoff: 1s, 2s, 4s, 8s, 16s).

### Sprint 1 (Days 2–4) — Baseline Text Generation
- [ ] Build basic prompt template taking text chunks from P2 retriever.
- [ ] Connect baseline generation pipeline to P4 UI.
- [ ] Evaluate Sprint 1 baseline on 20 sample questions.
- [ ] Log baseline failure modes (hallucinations, missed citations, lack of figures).

### Sprint 2 (Days 5–9) — Multimodal Grounding & Figure Embedding Engine
- [ ] Update context formatter to ingest `media_path` and `modality` fields from `chunks.json`.
- [ ] Design few-shot examples teaching the LLM when and how to embed figure plates.
- [ ] Implement post-generation validator:
  - Verify every markdown image tag points to an existing file in `data/extracted_media/`.
  - Strip broken or hallucinated file paths before rendering.
- [ ] Benchmark hallucination rate and modality embedding accuracy.

### Sprint 3 (Days 10–11) — Adversarial Hardening & Negative Constraint Tuning
- [ ] Test against 20+ edge-case questions (unanswerable questions, false premise questions).
- [ ] Tighten system prompt to prevent refusal breakdowns or over-confidence.
- [ ] Implement multi-source reconciliation prompt logic for conflicting lore documents.
- [ ] Measure final hallucination rate ($\le 5\%$).

### Sprint 4 (Days 12–13) — Report & Deliverables
- [ ] Write the **Generation, Prompt Engineering & Grounding** section of the 5-page report.
- [ ] Include prompt templates and before/after generation examples in report.
- [ ] Export LLM prompt conversation logs to `ai_usage/claude.md`.

### Sprint 5 (Day 14) — Defense Preparation
- [ ] Rehearse explaining prompt constraints, hallucination reduction mechanisms, and rate-limit handling to judges.

---

## 4. Resilience & Error Handling Checklist

| Error Condition | Expected Handling |
| :--- | :--- |
| **HTTP 429 (Rate Limit)** | Sleep with exponential backoff (1s, 2s, 4s, 8s, 16s); retry up to 5 times |
| **Primary Model Unavailable** | Automatic fallback to secondary OpenRouter model |
| **Invalid Image Path in LLM Output** | Regex post-processor replaces invalid path with fallback text note |
| **Empty Context from Retriever** | Courteous out-of-scope response without guessing |
