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
| **Claude 3.7 Sonnet / Claude 3.5 Sonnet** | Architectural brainstorming, drafting parser boilerplate, prompt engineering refinement | Sprints 0, 1, 2, 3 |
| **Google Antigravity (AGY)** | Pair programming assistant, file structure scaffolding, documentation formatting | Sprints 0, 1, 2, 4 |
| **OpenRouter / Meta Llama 3.3 70B** | Target runtime inference model for document answering and grounding evaluation | Sprints 1, 2, 3 |
| **Voyage AI (`voyage-4`)** | Dense text and caption embeddings for vector retrieval | Sprints 1, 2, 3 |

---

## 2. Human vs. AI Contributions & Decision Breakdown

### 2.1 Decisions Made Exclusively by the Human Team
1. **Sub-track Selection (1A):** The human team identified that enterprise value in the Ashen Era Archive lay in resolving schematics, plate diagrams, and tables rather than pure text summaries.
2. **Modality-Aware Chunking Architecture:** Conceiving the `chunks.json` contract and the separation of `text`, `table`, and `image-caption` chunks with direct file linking.
3. **Modality Score Weighting Formula:** Designing dynamic query intent detection and score boosting ($\mathbf{W}_{\text{modality}}$) rather than relying on an opaque end-to-end black-box model.
4. **Evaluation Protocol & Adversarial Testing:** Formulating the 4 quantitative metrics (Retrieval Precision, Citation Accuracy, Hallucination Rate, Modality Success Rate) and manually auditing answers against the 1,277-page corpus.
5. **System Hardening & Negative Constraints:** Diagnosing initial hallucination failures and writing strict negative grounding constraints into the system prompt.

### 2.2 Tasks Accelerated by AI Assistance
1. **Syntax & Boilerplate Generation:** Writing standard PyMuPDF image extraction filters and Streamlit component layouts.
2. **Regex & Markdown Parsing:** Drafting regular expressions for citation matching and table string formatting.
3. **Documentation Scaffolding:** Structuring markdown templates and formatting markdown tables.

---

## 3. Human Validation & Quality Assurance Protocol

- **No Unvalidated Code:** Every script generated or suggested by an AI tool was reviewed, modified, and locally tested on real Ashen Era corpus files by the assigned module lead.
- **Defense Readiness:** Every team member has reviewed all 4 modules and is prepared to explain, defend, and live-code modifications before the judging panel during the final round.
- **Chat Logs Exported:** Raw plain-text exports of all development chat sessions with AI assistants are preserved in `ai_usage/claude.md` and related files.
