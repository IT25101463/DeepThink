# Member P2 Workflow: Retrieval Lead

> **Owner:** Member P2  
> **Area of Responsibility:** Voyage AI Embeddings, Vector Indexing (ChromaDB), Query Intent Routing, Modality-Aware Retrieval & Ranking  
> **Key Deliverable:** `src/retrieval/` pipeline exposing `retrieve(query, top_k=5)` with modality weighting

---

## 1. Role Scope & Objectives

Traditional RAG retrievers perform purely semantic text-to-text matching. In Sub-track 1A, Member P2 must build a **Modality-Aware Retrieval Engine** that:
1. Embeds chunks from `chunks.json` using Voyage AI (`voyage-4`).
2. Persists and queries vectors efficiently in a local ChromaDB instance.
3. Detects whether a user query seeks visual schematics, structured data tables, or textual lore.
4. Dynamically weights chunk similarity scores to ensure relevant figure plates and tables are returned in top-k results.

---

## 2. Technical Interfaces & Contract

P2 provides the retrieval interface for P3 (Generation) and P4 (UI):

```python
from typing import List, Dict, Any

def retrieve(
    query: str, 
    top_k: int = 5, 
    modality_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k context chunks with modality-aware re-ranking.
    
    Returns:
        List of chunks matching the chunks.json schema with an added 'score' field.
    """
    ...
```

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — Alignment & API Setup
- [ ] Create Voyage AI account (dashboard.voyageai.com) and test API key generation.
- [ ] Verify test embedding call with `voyage-4` or `voyage-4-lite`.
- [ ] Set up local ChromaDB environment in `src/retrieval/`.
- [ ] Review `chunks.json` schema with P1.

### Sprint 1 (Days 2–4) — Baseline Vector Index
- [ ] Ingest baseline text chunks from P1 (`chunks.json`).
- [ ] Implement batch embedding pipeline with Voyage AI client (`batch_size=64`).
- [ ] Index vectors in ChromaDB with metadata payload (document, page, modality).
- [ ] Write naive `retrieve(query, k=5)` function based purely on cosine similarity.
- [ ] Test on 20 `sample_questions.json` and log baseline precision/recall in `docs/metrics.md`.

### Sprint 2 (Days 5–9) — Modality-Aware Retrieval Engine
- [ ] Ingest multimodal `chunks.json` (containing `text`, `table`, and `image-caption` chunks).
- [ ] Implement Query Intent Classifier / Heuristic Router:
  - Detect *Visual Intent* keywords (`diagram`, `plate`, `schematic`, `map`, `figure`, `look like`, `depicted`).
  - Detect *Tabular Intent* keywords (`table`, `specifications`, `stats`, `cost`, `numbers`, `matrix`).
- [ ] Implement Modality Score Boosting:
  $$\text{Score}(c) = \text{Sim}_{\text{Voyage}}(q, c) \times \begin{cases} 1.6 & \text{if } \text{modality} = \text{'image-caption'} \text{ and visual intent} \\ 1.4 & \text{if } \text{modality} = \text{'table'} \text{ and tabular intent} \\ 1.0 & \text{otherwise} \end{cases}$$
- [ ] Implement chunk deduplication and parent context expansion (fetching adjacent paragraphs for an image).
- [ ] Measure improvement on non-text questions from `sample_questions.json`.

### Sprint 3 (Days 10–11) — Retrieval Hardening & Tuning
- [ ] Stress test on 20+ adversarial edge-case queries authored by the team.
- [ ] Fine-tune modality boost weights to eliminate false positives (e.g. returning diagrams when text is requested).
- [ ] Implement hybrid lexical search (BM25 + Voyage dense vectors) if specific entity names or codex codes are missed.
- [ ] Update `docs/decisions.md` with ranking parameter choices.

### Sprint 4 (Days 12–13) — Report & Deliverables
- [ ] Write the **Retrieval & Modality-Aware Architecture** section of the 5-page report with comparison charts.
- [ ] Export AI chat sessions to `ai_usage/claude.md`.
- [ ] Verify index re-creation script (`python -m src.retrieval.indexer`) runs out of the box.

### Sprint 5 (Day 14) — Defense Preparation
- [ ] Prepare defense explanation for why Voyage AI was chosen, how modality boosting functions, and how the system generalizes.

---

## 4. Quality & Performance Checklist

| Target | Benchmark Requirement | Status / Method |
| :--- | :--- | :--- |
| **Token Frugality** | Stay well within Voyage 200M free token limit | Track token counter during batch runs |
| **Retrieval Latency** | $< 400\text{ms}$ per query | Benchmark with `time.perf_counter()` |
| **Modality Recall** | $\ge 90\%$ on image/table questions | Evaluated against `sample_questions.json` |
