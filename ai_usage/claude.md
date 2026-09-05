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

## Session Log 4: Groq LPU Hardware Acceleration & Local BGE Embeddings
- **Date:** 2026-09-01
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P3, P4
- **Summary:** Replaced cloud embedding dependencies with `BAAI/bge-small-en-v1.5` in local ChromaDB. Integrated Groq Cloud LPU (`openai/gpt-oss-120b`), cutting latency from 8.5s to 1.35s at 300+ tokens/sec.

```text
[Human]: Shared free-tier aggregators are hitting rate limits during multi-hop benchmarks. Can we make embeddings 100% local and accelerate inference to under 2 seconds?

[AI]: Yes. We can run BAAI/bge-small-en-v1.5 locally via SentenceTransformers in ChromaDB with zero network calls, and point our OpenAI-compatible client to Groq LPU endpoints using openai/gpt-oss-120b for 300+ tokens/sec.
```

---

## Session Log 5: Compound RAG 3.0 & Character Dossier Boosts
- **Date:** 2026-09-02
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P3 (Retrieval Lead)
- **Summary:** Debugged multi-hop relational retrieval failures (e.g. Brannoc Ironmere relationship to the Bleeding Crown). Added sub-query preservation, Primary Character Dossier boost (+0.35), and Multi-Entity intersection boost (+0.40).

```text
[Human]: The issue is retrieval failure: for relational questions like "difference between Brannoc Ironmere's membership and relationship to the Bleeding Crown", the query decomposer stripped the relational phrasing and the retriever missed the unacknowledged heir chunk. How do we fix this?

[AI]: We will preserve the full relational query in sub_queries[0] and inject dedicated bonuses in compute_cross_relevance: +0.35 when chunk matches the subject biography dossier and +0.40 when both the character and faction are present.
```

---

## Session Log 6: Strict Epistemic Restraint & Adaptive Budgeting
- **Date:** 2026-09-02
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P3, P4
- **Summary:** Human lead critiqued LLM output on the Purge of Blackport for inventing ungrounded narrative framing. Enforced Directive 5 strict non-extrapolation prompting and implemented 3-stage adaptive budgeting ($K=1..8$, Elbow drop-off $\alpha=0.60$, 2,500 token packing).

```text
[Human]: This verification is not 100% accurate. The archive does not explicitly explain that the discrepancy exists because of "divergent narrative framing". Never interpolate motives or speculative reasons. State what is recorded verbatim and admit the archive provides no reconciliation. Also, remove the manual Top-K sliders from the UI—the system must be autonomous.

[AI]: Understood. Updating Directive 5 in GROUNDED_SYSTEM_PROMPT to enforce strict epistemic restraint. Adding 3-stage adaptive budgeting (intent sizing, Elbow drop-off, token packing) and removing manual sliders from Streamlit.
```

---

## Session Log 7: Categorized Out-of-Scope Guardrails & Final Hardening
- **Date:** 2026-09-03
- **Assistant:** Claude 3.7 / Antigravity
- **Participants:** P3, P4
- **Summary:** Added 4 categorized out-of-scope fast-path refusal options (Real-world, Inappropriate/slurs, Physical sensors, Universal OOD), suppressed chunk inspect expander on refusals, and verified all 73 test suites.

```text
[Human]: Instead of giving the same generic refusal for "who is hitler" and slurs like "poda venna", can we have distinct options for out-of-scope queries with helpful archival suggestions, and suppress the chunk inspector?

[AI]: Implemented 4 categorized refusal buckets in router.py with 3 tailored exploration options each, wired UNIVERSAL_OOD_REFUSAL to CRAG, and suppressed the context expander in app.py when queries are rejected.
```
