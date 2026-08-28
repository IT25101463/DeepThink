# AI Chat History & Interaction Logs

In accordance with **SLIIT Codefest 2026 AI Usage Policy (Section 4.1 & 5.2)**, this file records the exported conversation logs with AI agents (Claude, ChatGPT, Antigravity) used during development.

---

## Session Log 1: Architecture & Team Workflow Planning
- **Date:** 2026-08-29
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P1, P2, P3, P4
- **Summary:** Established the 4-member roles, sprint breakdown (Sprints 0–5), `chunks.json` schema contract, and modality-aware retrieval design choice for Sub-track 1A.

```text
[Human]: We are competing in SLIIT Codefest 2026 AI Competition. We have selected Sub-track 1A (Rich Answers, Not Just Text) on the Ashen Era Archive. We have 4 members. How should we divide the work, design the architecture, and structure our sprints?

[AI]: Here is a structured team execution plan...
- P1: Ingestion & OCR Lead (chunks.json contract)
- P2: Retrieval Lead (Voyage AI + Modality-aware vector search)
- P3: Generation Lead (OpenRouter grounded prompting + inline figure embedding)
- P4: Interface & Documentation Lead (Streamlit UI + video demo + report)
...
```

---

## Session Log 2: Ingestion & Modality Contract Design
- **Date:** 2026-08-29
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P1 (Ingestion Lead)
- **Summary:** Designed the multimodal schema distinguishing `text`, `table`, and `image-caption` chunks with direct linking to extracted files in `data/extracted_media/`.

---

## Session Log 3: Rate-Limit Survival & Backoff Retry Strategy
- **Date:** 2026-08-29
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P2, P3
- **Summary:** Discussed handling HTTP 429 errors on OpenRouter and Voyage AI free tiers via exponential backoff (1s, 2s, 4s, 8s, 16s) and local embeddings caching.

---

*(Additional daily chat logs are continuously appended here throughout Sprints 1–4)*
