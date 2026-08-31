# Member P3 Workflow: Retrieval & Ranking Lead (Team Leader)

> **Owner:** Member P3 (Team Leader)  
> **Area of Responsibility:** 100% Free Local Vector Embeddings (BGE), Local ChromaDB Vector Store, Modality-Aware Query Intent Routing & Score Boosting  
> **Key Deliverables:** `src/retrieval/indexer.py`, `src/retrieval/router.py`, `src/retrieval/retriever.py`

---

## 1. Role Scope & Objectives

In **Sub-track 1A**, standard semantic search fails on image/table questions because it only matches text similarity. Member P3 builds a **Modality-Aware Retrieval Engine** that:
1. Embeds all chunks from `chunks.json` using **`BAAI/bge-small-en-v1.5`** locally with `sentence-transformers` (**100% Free, Zero Card, Zero API Key needed**).
2. Persists and queries vectors locally in ChromaDB.
3. Classifies incoming query intent (Visual / Tabular / Narrative text).
4. Dynamically weights chunk similarity scores to ensure figure plates and tables surface in top-k context.

---

## 2. Complete Execution Checklist (Today)

### Stage 1: Local Vector Indexer (`src/retrieval/indexer.py`)
- [ ] Read `data/chunks.json`.
- [ ] Initialize ChromaDB `SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5")`.
- [ ] Batch index chunks into local collection (`chroma_db/`) with metadata (`chunk_id`, `document_name`, `page_number`, `modality`, `media_path`, `caption`).

### Stage 2: Intent Router (`src/retrieval/router.py`)
- [ ] Implement keyword and heuristic classifier:
  - *Visual Intent:* `"diagram"`, `"figure"`, `"plate"`, `"schematic"`, `"map"`, `"illustration"`, `"look like"`, `"picture"` $\rightarrow$ `image-caption`
  - *Tabular Intent:* `"table"`, `"specs"`, `"specifications"`, `"stats"`, `"cost"`, `"matrix"`, `"dimensions"` $\rightarrow$ `table`
  - *Text Intent:* Default lore narrative $\rightarrow$ `text`

### Stage 3: Modality-Aware Retriever (`src/retrieval/retriever.py`)
- [ ] Implement `retrieve(query, top_k=5)`.
- [ ] Query ChromaDB for top 15 candidate vectors.
- [ ] Apply dynamic modality boosting:
  $$\text{Score}(c) = \text{CosineSim}(q, c) \times \begin{cases} 1.6 & \text{if chunk is 'image-caption' and visual intent} \\ 1.4 & \text{if chunk is 'table' and tabular intent} \\ 1.0 & \text{otherwise} \end{cases}$$
- [ ] Return top 5 ranked chunks for P4 generation engine.

---

## 3. Interface Contract

```python
from typing import List, Dict, Any

def retrieve(
    query: str, 
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k context chunks with modality-aware boosting.
    """
    ...
```
