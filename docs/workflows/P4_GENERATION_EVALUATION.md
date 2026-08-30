# Member P4 Workflow: Generation, Evaluation & Delivery Lead

> **Owner:** Member P4  
> **Area of Responsibility:** OpenRouter LLM Grounding & Citations, Automated Benchmark Evaluation Suite, Streamlit Web Interface, Demo Video Production & 5-Page Submission Report  
> **Key Deliverables:** `src/generation/generator.py`, `src/evaluation/evaluator.py`, `src/ui/app.py`, 10-Minute YouTube Demo Video, 5-Page `submission_report.pdf`

---

## 1. Role Scope & Objectives

Rather than spending two weeks on superficial UI styling, Member P4 focuses on what wins marks on the judging rubric:
1. **Grounded Generation & Citation Enforcement:** Ensuring the LLM embeds relevant figures/tables (`![Caption](media_path)`) and strictly cites `[Document Name, Page Number]` with zero hallucinations.
2. **Automated Evaluation & Benchmarking:** Authoring and running automated evaluation test suites across the 20 sample questions to prove measurable before/after improvement.
3. **Streamlit UI Integration:** Connecting Ingestion (P1/P2), Retrieval (P3), and Generation (P4) into a clean, working web interface.
4. **Final Deliverables:** Recording and editing the 10-minute demo video and compiling the 5-page submission report.

---

## 2. System Prompt & Grounding Contract

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

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — OpenRouter Setup & Evaluation Skeletons
- [ ] Set up OpenRouter account (openrouter.ai) and configure free/cheap models (`meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-chat`).
- [ ] Implement exponential backoff retry handler (`tenacity` or custom loop: 1s, 2s, 4s, 8s, 16s) to survive rate limits.
- [ ] Initialize Streamlit environment (`src/ui/app.py`).
- [ ] Create automated evaluation test skeleton (`src/evaluation/evaluator.py`).

### Sprint 1 (Days 2–4) — Baseline Generator & UI Skeleton
- [ ] Connect OpenRouter generator to P3 baseline retriever.
- [ ] Build minimal Streamlit chat interface allowing user text input and displaying generated answers.
- [ ] Run baseline evaluation on the 20 sample questions: calculate precision, citation accuracy, and hallucination rate.
- [ ] Log baseline failure modes in `docs/metrics.md` (e.g. failing on visual/table queries).

### Sprint 2 (Days 5–9) — Multimodal Grounding & Rich Streamlit Display (Core Feature)
- [ ] Update generator to process multimodal context with `media_path` and `modality`.
- [ ] Implement strict citation enforcement and `![Caption](media_path)` injection.
- [ ] Add post-generation validator to verify all embedded media paths exist on disk before rendering.
- [ ] In Streamlit UI: render embedded figures, diagrams, and markdown tables cleanly alongside text.
- [ ] Add expandable citation sidebar showing source chunks, similarity scores, and reliability badges.
- [ ] Re-run evaluation on all 20 sample questions and update `docs/metrics.md` showing measurable improvement.

### Sprint 3 (Days 10–11) — Adversarial Testing & Hallucination Elimination
- [ ] Run stress tests on 20+ adversarial questions authored by the team.
- [ ] Tighten negative prompt constraints to bring hallucination rate to $0\%$.
- [ ] Test UI edge cases (spinner during backoff retry, error toast handling).
- [ ] Document limitations and failed experiments in `docs/limitations.md`.

### Sprint 4 (Days 12–13) — Demo Video Production & 5-Page Report
- [ ] **Record Demo Video ($\le 10$ mins total):**
  - Segment 1: Problem statement & architecture overview (2–3 mins).
  - Segment 2: **Live unedited screen recording demo** answering real questions with embedded figures/tables (3–4 mins mandatory).
  - Segment 3: Technical decisions, metrics comparison, and limitations (2–3 mins).
- [ ] Upload video to YouTube as **Unlisted**; test link accessibility in incognito.
- [ ] Compile the **5-page PDF submission report** (`submission_report.pdf`):
  - Paste YouTube unlisted link at top of page 1.
  - Include problem statement, architecture diagrams, decision analysis, limitations, AI disclosure, and team contributions.
- [ ] Finalize `ai_usage/ai-usage-disclosure.md` with contributions from P1, P2, P3.

### Sprint 5 (Day 14) — Pre-Submission Audit & ZIP Packaging
- [ ] Run `git log` and `git status` audit: ensure zero leaked keys or uncommitted tracked `.env` files.
- [ ] Test fresh repository clone on clean environment (`pip install -r requirements.txt`).
- [ ] Create clean `<Team_Name>.zip` archive including the complete `.git` directory.
- [ ] Submit before 9 September 2026, 11:30 PM.

---

## 4. Deliverables & Evaluation Checklist

| Deliverable | Target Requirement | Status / Verification |
| :--- | :--- | :--- |
| **Hallucination Rate** | $\le 5\%$ (Target: 0%) | Evaluated via manual & automated checks |
| **Modality Success Rate** | $\ge 90\%$ on image/table questions | Evaluated in `docs/metrics.md` |
| **Demo Video** | $\le 10$ mins, $\ge 3-4$ min live unedited demo, Unlisted YouTube | YouTube link tested in incognito |
| **Submission Report** | Max 5 pages, PDF format, contains YouTube link & diagrams | Page count strictly $\le 5$ |
| **Git Repository** | ZIP with full `.git` history, zero API keys, README instructions | Tested fresh unzip & run |
