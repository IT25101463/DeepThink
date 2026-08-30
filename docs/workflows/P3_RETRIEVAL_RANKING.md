# Member P3 Workflow: Retrieval & Reranking Lead

> **Owner:** Member P3  
> **Area of Responsibility:** Voyage AI Embeddings, Local ChromaDB Vector Store, Modality-Aware Query Intent Routing, Voyage `rerank-2.5` Reranking  
> **Key Deliverables:** `src/retrieval/indexer.py`, `src/retrieval/router.py`, `src/retrieval/retriever.py`

---

## 1. Role Scope & Objectives

In **Sub-track 1A**, standard semantic search fails on image/table questions because it only matches text similarity. Member P3 builds a **Modality-Aware Retrieval & Reranking Engine** that:
1. Embeds all chunks from `chunks.json` using Voyage AI (`voyage-4`) within the 200M free token tier.
2. Persists and queries vectors locally in ChromaDB.
3. Classifies incoming query intent (Visual / Tabular / Narrative text).
4. Dynamically weights chunk similarity scores to ensure figure plates and tables surface in top-k context.
5. Applies Voyage `rerank-2.5` to re-rank candidate chunks for high precision.

---

## 2. Technical Interface Contract

```python
from typing import List, Dict, Any, Optional

def retrieve(
    query: str, 
    top_k: int = 5, 
    rerank: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k context chunks with modality-aware boosting and Voyage reranking.
    
    Returns:
        List of chunk dicts matching chunks.json schema with an added 'relevance_score' field.
    """
    ...
```

---

## 3. Sprint-by-Sprint Execution Plan

### Sprint 0 (Day 1) — Voyage AI & ChromaDB Setup
- [ ] Create Voyage AI account (dashboard.voyageai.com) and test API key.
- [ ] Set up local ChromaDB environment in `src/retrieval/`.
- [ ] Review `chunks.json` schema contract with P1 and P2.

### Sprint 1 (Days 2–4) — Baseline Vector Search
- [ ] Ingest baseline text chunks from P1 (`data/chunks.json`).
- [ ] Implement batch embedding pipeline with Voyage AI (`voyage-4`, `batch_size=64`).
- [ ] Index vectors in ChromaDB with metadata payload (document, page, modality).
- [ ] Implement basic `retrieve(query, top_k=5)` using standard cosine similarity.
- [ ] Benchmark baseline retrieval precision on the 20 sample questions.

### Sprint 2 (Days 5–9) — Modality-Aware Routing & Voyage Reranking (Core Engine)
- [ ] Ingest full multimodal `chunks.json` (containing `text`, `table`, and `image-caption` chunks).
- [ ] Implement **Query Intent Classifier**:
  - Detect *Visual Intent* keywords (`diagram`, `plate`, `schematic`, `map`, `figure`, `look like`, `depicted`).
  - Detect *Tabular Intent* keywords (`table`, `specifications`, `stats`, `cost`, `numbers`, `matrix`).
- [ ] Implement **Modality Score Boosting**:
  $$\text{Score}(c) = \text{Sim}_{\text{Voyage}}(q, c) \times \begin{cases} 1.6 & \text{if } \text{modality} = \text{'image-caption'} \text{ and visual intent} \\ 1.4 & \text{if } \text{modality} = \text{'table'} \text{ and tabular intent} \\ 1.0 & \text{otherwise} \end{cases}$$
- [ ] Integrate Voyage AI `rerank-2.5` to re-order top 15 candidate chunks down to the top 5 most relevant chunks.
- [ ] Measure retrieval precision/recall leap from Sprint 1 baseline to Sprint 2.

### Sprint 3 (Days 10–11) — Retrieval Hardening & Hybrid Search
- [ ] Author and test 20+ adversarial search queries (uncommon names, obscure artifacts).
- [ ] Implement hybrid search (BM25 lexical matching + Voyage dense vectors) to handle exact proper nouns.
- [ ] Fine-tune modality boost weights to eliminate false-positive image retrieval.
- [ ] Benchmark retrieval latency (ensure $< 500\text{ms}$ per query).

### Sprint 4 (Days 12–13) — Report Contribution & Architecture Documentation
- [ ] Write the **Modality-Aware Retrieval, Intent Routing & Reranking** section of the 5-page report.
- [ ] Include retrieval precision/recall charts and before/after comparisons.
- [ ] Export AI prompt interaction logs to `ai_usage/claude.md`.

### Sprint 5 (Day 14) — Defense Preparation
- [ ] Rehearse explaining vector space properties, modality boosting equations, and reranking strategy to the judges.

---

## 4. Performance & Quality Targets

| Metric | Target | Verification Method |
| :--- | :--- | :--- |
| **Embedding Quota** | $< 10\text{M}$ tokens (well within 200M limit) | Voyage dashboard token tracking |
| **Retrieval Top-5 Precision** | $\ge 90\%$ | Tested against `sample_questions.json` |
| **Image/Table Retrieval Rate** | $\ge 90\%$ on visual questions | Evaluated in `docs/metrics.md` |
