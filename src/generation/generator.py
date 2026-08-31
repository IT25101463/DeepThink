"""
Grounded Generation Engine (Owner: Member P4 - Generation, Evaluation & Delivery Lead)
Calls OpenRouter LLM, enforces citations, embeds media links, and handles rate-limit retries.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import (
    OPENROUTER_API_KEY, 
    LLM_MODEL_NAME, 
    PROJECT_ROOT, 
    EXTRACTED_MEDIA_DIR
)

logger = logging.getLogger("deepthink.generator")

# Strict System Prompt for Sub-track 1A
GROUNDED_SYSTEM_PROMPT = """You are DeepThink, an expert enterprise document assistant for the Ashen Era Archive.
You answer user questions using ONLY the retrieved context chunks provided below.

RULES:
1. STRICT GROUNDING: Rely exclusively on facts in the retrieved context.
   If information is absent or unverified, state: "The archive records do not specify [detail]."
2. PRECISE CITATIONS: Cite the exact document and page number for every claim using:
   [Document Name, Page X].
3. INLINE FIGURE & TABLE EMBEDDING (CRITICAL):
   When context contains a chunk with modality 'image-caption' or 'table' and a valid media_path,
   you MUST embed the figure directly in your markdown answer:
   ![Figure Caption](media_path)
   Place the image directly adjacent to the relevant explanatory text.
4. SOURCE CONFLICT RESOLUTION:
   Highlight discrepancies between official codex records and ephemera/tavern songs."""


def format_context_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Constructs the grounded prompt containing context snippets, source tags, and media paths.
    """
    if not chunks:
        return f"User Query: {query}\n\nNo relevant context chunks retrieved from the archive."

    context_lines = [f"User Query: {query}\n\nRetrieved Archive Context Chunks:"]
    for i, c in enumerate(chunks, 1):
        doc = c.get("document_name", "Unknown")
        page = c.get("page_number", 1)
        modality = c.get("modality", "text")
        media = c.get("media_path", "")
        caption = c.get("caption", "")
        content = c.get("content", "")
        section = c.get("section_title", "")
        
        # Determine source reliability
        custom_meta = c.get("metadata", {})
        reliability = c.get("source_reliability")
        if not reliability and isinstance(custom_meta, dict):
            reliability = custom_meta.get("source_reliability", "archive_record")
        if not reliability:
            reliability = "archive_record"

        chunk_header = f"\n--- [Chunk {i}] Source: {doc} (Page {page}) | Modality: {modality} | Reliability: {reliability}"
        if section:
            chunk_header += f" | Section: {section}"
        context_lines.append(chunk_header)

        if media:
            norm_media = str(media).replace("\\", "/")
            context_lines.append(f"Media Path: {norm_media}")
        if caption:
            context_lines.append(f"Caption: {caption}")
        context_lines.append(f"Content:\n{content}")

    return "\n".join(context_lines)


def resolve_media_path(media_path: str) -> Optional[str]:
    """
    Validates and resolves a media file path on disk.
    Returns normalized relative path with forward slashes if valid, else None.
    """
    if not media_path:
        return None

    cleaned_path = media_path.strip().strip("'\"").replace("\\", "/")
    
    # Try as direct path or relative to project root
    candidate_paths = [
        Path(cleaned_path),
        PROJECT_ROOT / cleaned_path,
        PROJECT_ROOT / "data" / cleaned_path,
        EXTRACTED_MEDIA_DIR / cleaned_path,
        EXTRACTED_MEDIA_DIR / "figures" / Path(cleaned_path).name,
        EXTRACTED_MEDIA_DIR / "tables" / Path(cleaned_path).name
    ]

    for p in candidate_paths:
        try:
            if p.exists() and p.is_file():
                # Return path relative to PROJECT_ROOT formatted with forward slashes
                try:
                    rel_path = p.resolve().relative_to(PROJECT_ROOT.resolve())
                    return str(rel_path).replace("\\", "/")
                except ValueError:
                    return str(p).replace("\\", "/")
        except Exception:
            continue

    return None


def verify_and_fix_media_paths(response_text: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Scans markdown image tags in response, normalizes paths, verifies disk existence,
    and automatically injects visual figure plates from context if omitted by LLM.
    """
    # 1. Normalize existing image tags in response
    image_pattern = r"!\[(.*?)\]\((.*?)\)"
    
    def _replace_image_tag(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        resolved = resolve_media_path(img_path)
        if resolved:
            return f"![{alt_text}]({resolved})"
        # If path could not be resolved directly, search context chunks for a matching filename
        img_filename = Path(img_path).name
        for c in context_chunks:
            c_media = c.get("media_path")
            if c_media and Path(c_media).name == img_filename:
                c_resolved = resolve_media_path(c_media)
                if c_resolved:
                    return f"![{alt_text or c.get('caption', 'Figure')}]({c_resolved})"
        return match.group(0)

    fixed_text = re.sub(image_pattern, _replace_image_tag, response_text)

    # 2. Auto-injection: If context contains high-relevance visual/table chunk and no image was embedded
    has_image_tag = "![" in fixed_text
    if not has_image_tag and context_chunks:
        for chunk in context_chunks:
            modality = chunk.get("modality", "")
            media_path = chunk.get("media_path")
            if (modality in ("image-caption", "table") or media_path) and media_path:
                resolved = resolve_media_path(media_path)
                if resolved:
                    caption = chunk.get("caption") or chunk.get("section_title") or "Archival Figure Plate"
                    doc = chunk.get("document_name", "Archive Record")
                    page = chunk.get("page_number", 1)
                    injection = (
                        f"\n\n![{caption}]({resolved})\n"
                        f"*Figure: {caption} — [{doc}, Page {page}]*"
                    )
                    fixed_text = fixed_text.strip() + injection
                    break

    return fixed_text


def synthesize_grounded_fallback(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Deterministic offline context synthesizer that generates grounded,
    hallucination-free answers with precise citations and media embeds directly from retrieved chunks.
    Used when API key is not configured or OpenRouter is unreachable.
    """
    if not context_chunks:
        return "The archive records do not specify any verified information regarding this query."

    # Identify primary matching chunk
    top_chunk = context_chunks[0]
    doc = top_chunk.get("document_name", "Archive Record")
    page = top_chunk.get("page_number", 1)
    modality = top_chunk.get("modality", "text")
    content = top_chunk.get("content", "").strip()
    caption = top_chunk.get("caption", "")
    media_path = top_chunk.get("media_path")

    # Check for visual plates
    visual_chunks = [c for c in context_chunks if c.get("modality") == "image-caption" or c.get("media_path")]
    table_chunks = [c for c in context_chunks if c.get("modality") == "table"]

    response_parts = []

    # 1. Main factual synthesis
    if visual_chunks:
        v_chunk = visual_chunks[0]
        v_doc = v_chunk.get("document_name", doc)
        v_page = v_chunk.get("page_number", page)
        v_caption = v_chunk.get("caption") or v_chunk.get("content", "")
        v_media = v_chunk.get("media_path")
        
        resolved_media = resolve_media_path(v_media) if v_media else None
        
        response_parts.append(f"Based on the official archival records in [{v_doc}, Page {v_page}]:")
        response_parts.append(f"\n{v_chunk.get('content', '')}")
        
        if resolved_media:
            caption_clean = v_caption if v_caption else "Official Archive Figure Plate"
            response_parts.append(f"\n\n![{caption_clean}]({resolved_media})")
            response_parts.append(f"\n*Figure: {caption_clean} — Source: [{v_doc}, Page {v_page}]*")

    elif table_chunks:
        t_chunk = table_chunks[0]
        t_doc = t_chunk.get("document_name", doc)
        t_page = t_chunk.get("page_number", page)
        
        response_parts.append(f"According to the structured codex records in [{t_doc}, Page {t_page}]:\n")
        response_parts.append(t_chunk.get("content", ""))
        
    else:
        # Text narrative
        response_parts.append(f"According to archive records in [{doc}, Page {page}]:\n")
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if paragraphs:
            response_parts.append(paragraphs[0])
            if len(paragraphs) > 1:
                response_parts.append("\n" + paragraphs[1])
        else:
            response_parts.append(content)

    # 2. Check for corroborating or conflicting accounts in subsequent chunks
    conflicts = []
    for c in context_chunks[1:3]:
        c_rel = c.get("source_reliability") or (c.get("metadata", {}).get("source_reliability") if isinstance(c.get("metadata"), dict) else "")
        if c_rel in ("ephemera", "ballad", "tavern_song", "unverified"):
            c_doc = c.get("document_name", "Ephemera")
            c_page = c.get("page_number", 1)
            conflicts.append(f"- *Contrasting account from ephemera source* [{c_doc}, Page {c_page}]: \"{c.get('content', '')[:120]}...\"")

    if conflicts:
        response_parts.append("\n\n**Archival Discrepancy Note:**")
        response_parts.extend(conflicts)

    return "\n".join(response_parts)


def generate_with_openrouter(
    query: str, 
    context_chunks: List[Dict[str, Any]], 
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Executes grounded LLM generation via OpenRouter OpenAI-compatible API with retry resilience.
    """
    try:
        import openai
        from openai import OpenAI, RateLimitError, APIConnectionError, InternalServerError
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    except ImportError as e:
        logger.warning(f"Required generation libraries not installed ({e}). Using grounded fallback.")
        return synthesize_grounded_fallback(query, context_chunks)

    active_api_key = api_key or OPENROUTER_API_KEY
    if not active_api_key or active_api_key.startswith("sk-or-v1-placeholder") or len(active_api_key) < 15:
        logger.info("No active OpenRouter API key found. Using deterministic grounded fallback.")
        return synthesize_grounded_fallback(query, context_chunks)

    active_model = model or LLM_MODEL_NAME

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=active_api_key,
        timeout=12.0,
        default_headers={
            "HTTP-Referer": "https://github.com/IT25101463/DeepThink",
            "X-Title": "DeepThink Ashen Era Assistant"
        }
    )

    formatted_context = format_context_prompt(query, context_chunks)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, InternalServerError)),
        reraise=True
    )
    def _call_api():
        completion = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                {"role": "user", "content": formatted_context}
            ],
            temperature=0.1,
            max_tokens=1024
        )
        return completion.choices[0].message.content

    try:
        raw_response = _call_api()
        return verify_and_fix_media_paths(raw_response, context_chunks)
    except Exception as e:
        logger.warning(f"OpenRouter API call failed ({e}). Utilizing grounded fallback.")
        fallback_res = synthesize_grounded_fallback(query, context_chunks)
        return verify_and_fix_media_paths(fallback_res, context_chunks)


def generate_answer(
    query: str, 
    context_chunks: List[Dict[str, Any]], 
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Main generator interface: synthesizes grounded answer with citations and verified media links.
    """
    if not query or not query.strip():
        return "Please ask a question about the Ashen Era Archive."

    response = generate_with_openrouter(
        query=query, 
        context_chunks=context_chunks, 
        model=model, 
        api_key=api_key
    )
    
    return response


if __name__ == "__main__":
    sample_chunk = [{
        "chunk_id": "test_plate_00",
        "document_name": "codex_vaeloria_i.pdf",
        "page_number": 12,
        "modality": "image-caption",
        "content": "Official Codex Vaeloria figure plate for Marrowwatch showing Recorded Garrison Strength: 3,107 souls under arms.",
        "media_path": "data/extracted_media/figures/plate_00_location_marrowwatch.png",
        "caption": "Figure Plate: Marrowwatch Recorded Garrison Strength",
        "metadata": {"source_reliability": "official_codex"}
    }]
    
    ans = generate_answer("What is the recorded garrison strength of Marrowwatch?", sample_chunk)
    print("--- Generated Answer ---")
    print(ans)
