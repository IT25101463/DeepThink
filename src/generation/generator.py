"""
Grounded Generation Engine (Owner: Member P4)
Calls OpenRouter LLM, enforces citations, embeds media links, and handles rate-limit retries.
"""

from typing import List, Dict, Any
from src.config import OPENROUTER_API_KEY, LLM_MODEL_NAME


def format_context_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Constructs the grounded prompt containing context snippets, source tags, and media paths.
    """
    context_text = ""
    for i, c in enumerate(chunks, 1):
        doc = c.get("document_name", "Unknown")
        page = c.get("page_number", "?")
        modality = c.get("modality", "text")
        media = c.get("media_path", "")
        content = c.get("content", "")
        
        context_text += f"\n[Chunk {i}] Source: {doc} (Page {page}) | Modality: {modality}\n"
        if media:
            context_text += f"Media Path: {media}\n"
        context_text += f"Content: {content}\n"
        
    return context_text


def generate_answer(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Generates grounded response using OpenRouter API with exponential backoff retry.
    """
    # TODO (P4): Implement OpenAI client pointing to https://openrouter.ai/api/v1 with tenacity retry
    return "Placeholder response from DeepThink generator."
