"""
Retrieval Package: 100% Free Local BGE Vector Indexing, Modality Intent Routing, and Re-ranking.
Owner: Member P3 (Retrieval & Ranking Lead / Team Leader)
"""

# Lazy / clean exports to avoid runpy module import warnings
def index_chunks(*args, **kwargs):
    from src.retrieval.indexer import index_chunks as _index_chunks
    return _index_chunks(*args, **kwargs)

def retrieve(*args, **kwargs):
    from src.retrieval.retriever import retrieve as _retrieve
    return _retrieve(*args, **kwargs)

def analyze_query_intent(*args, **kwargs):
    from src.retrieval.router import analyze_query_intent as _analyze
    return _analyze(*args, **kwargs)

def detect_modality_intent(*args, **kwargs):
    from src.retrieval.router import detect_modality_intent as _detect
    return _detect(*args, **kwargs)

__all__ = [
    "index_chunks",
    "retrieve",
    "analyze_query_intent",
    "detect_modality_intent"
]
