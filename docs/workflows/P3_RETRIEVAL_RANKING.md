# Member P3 Workflow: Retrieval & Reranking Lead (Team Leader)

> **Owner:** Member P3 (Team Leader)  
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

## 2. Complete Execution Checklist (Today)

### Stage 1: Vector Indexer (`src/retrieval/indexer.py`)
- [ ] Read `data/chunks.json`.
- [ ] Connect Voyage AI client using `VOYAGE_API_KEY` (model: `voyage-4`).
- [ ] Implement batch embedding with progress bar (`tqdm`, `batch_size=64`).
- [ ] Initialize persistent local ChromaDB collection (`chroma_db/`) with metadata (`chunk_id`, `document_name`, `page_number`, `modality`, `media_path`, `caption`).

### Stage 2: Intent Router (`src/retrieval/router.py`)
- [ ] Implement keyword and heuristic classifier:
  - *Visual Intent:* `"diagram"`, `"figure"`, `"plate"`, `"schematic"`, `"map"`, `"illustration"`, `"look like"`, `"picture"` $\rightarrow$ `image-caption`
  - *Tabular Intent:* `"table"`, `"specs"`, `"specifications"`, `"stats"`, `"cost"`, `"matrix"`, `"dimensions"` $\rightarrow$ `table`
  - *Text Intent:* Default lore narrative $\rightarrow$ `text`

### Stage 3: Modality-Aware Retriever (`src/retrieval/retriever.py`)
- [ ] Implement `retrieve(query, top_k=5, rerank=True)`.
- [ ] Query ChromaDB for top 15 candidate vectors.
- [ ] Apply dynamic modality boosting:
  $$\text{Score}(c) = \text{Sim}(q, c) \times \begin{cases} 1.6 & \text{if chunk is 'image-caption' and visual intent} \\ 1.4 & \text{if chunk is 'table' and tabular intent} \\ 1.0 & \text{otherwise} \end{cases}$$
- [ ] Apply Voyage AI `rerank-2.5` to produce the final top 5 grounded context chunks.

---

## 3. Interface Contract

```python
from typing import List, Dict, Any

def retrieve(
    query: str, 
    top_k: int = 5, 
    rerank: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k context chunks with modality-aware boosting and Voyage reranking.
    """
    ...
```
