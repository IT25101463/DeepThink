# Member P4 Workflow: Interface & Documentation Lead

> **Owner:** Member P4  
> **Area of Responsibility:** Streamlit Web Application, Rich Media Inline Rendering, UI/UX, Documentation, Architecture Diagrams, Demo Video Recording & Submission Packaging  
> **Key Deliverable:** `src/ui/app.py`, 10-Minute YouTube Demo Video, 5-Page `submission_report.pdf`, and final clean ZIP archive

---

## 1. Role Scope & Objectives

A strong technical solution needs clear, polished presentation and robust documentation. Member P4 bridges the engineering modules into a clean product and leads the team's presentation deliverables.

Member P4 is responsible for:
1. **Interactive UI (`src/ui/app.py`):** Building a modern Streamlit interface that renders rich markdown, images, tables, citations, and inspectable retrieved context.
2. **Documentation & ADRs:** Maintaining `README.md`, `docs/architecture.md`, `docs/decisions.md`, `docs/limitations.md`, and `docs/metrics.md`.
3. **Demonstration Video:** Recording and editing the $\le 10$-minute demo video featuring a 3–4 minute unedited live screen demo.
4. **Submission Report & Packaging:** Compiling the 5-page PDF report and preparing the final ZIP archive with clean git commit history.

---

## 2. UI Specifications (`src/ui/app.py`)

The Streamlit interface must provide:
- **Chat Interface:** Clean message history with user input box.
- **Rich Media Viewport:** Dynamic rendering of embedded figure plates, maps, diagrams, and formatted markdown tables.
- **Source Inspection Drawer / Sidebar:** Clickable expanders showing the exact retrieved chunks, similarity scores, modality tags, and source document metadata.
- **Modality Filter Controls (Optional for Demo):** Toggle to show/hide retrieval diagnostics and compare naive vs modality-aware results live.

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — Alignment & Repository Architecture
- [ ] Initialize repository structure per Section 5.2 format.
- [ ] Ensure `.gitignore` ignores `.env` and sensitive files from the very first commit.
- [ ] Setup `README.md` and documentation skeletons in `docs/`.
- [ ] Verify Streamlit environment setup.

### Sprint 1 (Days 2–4) — Baseline UI & Module Integration
- [ ] Build minimal Streamlit chat interface connecting to P2 (Retrieval) and P3 (Generation).
- [ ] Test end-to-end question answering pipeline on Day 4 milestone.
- [ ] Draft initial system architecture diagram in `docs/diagrams/`.
- [ ] Record initial baseline screenshots.

### Sprint 2 (Days 5–9) — Rich Multimodal UI & Live Decision Tracking
- [ ] Enhance UI to seamlessly display inline images and side-by-side table comparisons.
- [ ] Add expandable citation pills showing document name, page number, and reliability badge.
- [ ] Document all design decisions in `docs/decisions.md` in real time.
- [ ] Maintain `docs/metrics.md` with Sprint 2 benchmark results.

### Sprint 3 (Days 10–11) — UI Hardening & Limitations Documentation
- [ ] Handle UI edge cases (broken images, loading spinners during backoff retries, error toast notifications).
- [ ] Compile honest appraisal of system limitations in `docs/limitations.md`.
- [ ] Design slides and visual assets for the demo video presentation segment.

### Sprint 4 (Days 12–13) — Video Production & 5-Page Report Compilation
- [ ] **Record Demo Video ($\le 10$ min total):**
  - Segment 1: Problem statement & architecture slides (2–3 mins).
  - Segment 2: **Live unedited screen recording demo** answering real questions with embedded figures/tables (3–4 mins mandatory).
  - Segment 3: Technical decisions, metrics comparison, and limitations (2–3 mins).
- [ ] Upload video to YouTube as **Unlisted**; test link accessibility in incognito.
- [ ] Compile and format the **5-page PDF submission report** (`submission_report.pdf`):
  - Paste YouTube unlisted link at top of page 1.
  - Include problem statement, architecture diagrams, decision analysis, limitations, AI disclosure, and team contributions.
- [ ] Finalize `ai_usage/ai-usage-disclosure.md` with inputs from P1, P2, P3.

### Sprint 5 (Day 14) — Pre-Submission Audit & ZIP Packaging
- [ ] Run `git log` and `git status` audit: ensure zero leaked keys or uncommitted tracked `.env` files.
- [ ] Test that a new user can clone repo, run `pip install -r requirements.txt`, and launch app without errors.
- [ ] Create clean `<Team_Name>.zip` archive including the complete `.git` directory.
- [ ] Submit before 9 September 2026, 11:30 PM.

---

## 4. Deliverables Checklist

| Deliverable | Target Requirement | Status / Verification |
| :--- | :--- | :--- |
| **Demo Video** | $\le 10$ mins, $\ge 3-4$ min live unedited demo, Unlisted YouTube | YouTube link tested in incognito |
| **Submission Report** | Max 5 pages, PDF format, contains YouTube link & diagrams | Page count strictly $\le 5$ |
| **Git Repository** | ZIP with full `.git` history, zero API keys, README instructions | Tested fresh unzip & run |
| **AI Disclosure** | `ai_usage/ai-usage-disclosure.md` complete + raw chat logs | Verified in repo |
