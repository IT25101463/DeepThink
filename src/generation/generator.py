"""
Grounded Generation Engine (Owner: Member P4 - Generation, Evaluation & Delivery Lead)
Calls Groq Cloud API (300+ tokens/sec LPU inference), enforces citations, embeds media links,
handles rate-limit retries, and enforces airtight domain guardrails for out-of-scope queries.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.config import (
    GROQ_API_KEY,
    LLM_MODEL_NAME, 
    PROJECT_ROOT, 
    EXTRACTED_MEDIA_DIR
)

logger = logging.getLogger("deepthink.generator")

# Standard Polite Domain Refusal Message
OUT_OF_SCOPE_REFUSAL = (
    "I am DeepThink, specialized exclusively in analyzing the Ashen Era Archive documentation. "
    "Your inquiry is outside the scope of this archival repository. "
    "Please feel free to ask questions regarding Ashen Era history, faction chronicles, codex schematics, artillery specifications, or trial records."
)

GREETING_MESSAGE = (
    "Greetings! I am **DeepThink**, your dedicated multimodal archival assistant for the Ashen Era Archive. "
    "How may I assist you with historical chronicles, battle accords, codex schematics, or ledger records today?"
)

# Strict Grounded Scholarly System Prompt for Sub-track 1A (High Intelligence & Specificity)
GROUNDED_SYSTEM_PROMPT = """You are DeepThink, the master archival intelligence and senior scholar of the Ashen Era Archive.
You provide deeply intelligent, comprehensive, and laser-specific analyses of archival documentation using ONLY the retrieved context chunks provided below.

CORE OPERATING DIRECTIVES:

1. INTELLIGENCE, DEPTH & SPECIFICITY (SCHOLARLY RIGOR):
   - Provide thorough, intellectually rigorous, and complete explanations. Never provide shallow, lazy, or one-sentence summaries.
   - Synthesize all relevant facts across ALL provided context chunks into a coherent, structured, and nuanced historical narrative.
   - Always extract and include exact proper names, honorific titles, dates, geographical regions, troop strengths, battle casualty numbers, artifact specifications, ledger sums, and architectural dimensions whenever present in the context.
   - Use professional Markdown formatting: bold key entities (**The Ashen Vanguard**, **Halvard Cindervale**), use structured bullet points for multi-part breakdowns, and use bold section headers where appropriate.

2. ZERO FLUFF & DIRECT SCHOLARLY TONE:
   - Speak with the authoritative, objective voice of an elite historical archivist.
   - Avoid generic conversational filler such as "Based on the text provided...", "Sure, I can help with that...", or "Here is what I found...".
   - Start directly with the synthesized answer and core historical truth.

3. PRECISE IN-TEXT CITATIONS:
   - Every factual claim, statistic, entity mention, or historical assertion MUST be immediately substantiated with an exact bracket citation:
     [Document Name, Page X].
   - If multiple documents corroborate a fact, cite all relevant sources: [Doc1, Page X; Doc2, Page Y].

4. SUB-TRACK 1A: MULTIMODAL INLINE FIGURE & TABLE EMBEDDINGS:
   - When a retrieved chunk contains a visual figure plate or table with a valid `media_path`, you MUST embed the figure directly into your response:
     ![Descriptive Caption](media_path)
   - Accompany every embedded figure with explanatory analysis explaining what the visual plate depicts according to archival records.

5. SOURCE CONFLICT RESOLUTION & EPISTEMIC HUMILITY:
   - Distinguish between official codex annals and unreliable in-world ephemera (tavern ballads, prisoner testimonies, intercepted letters). Explicitly note archival discrepancies when sources disagree.
   - If a specific detail is unrecorded in the archive, explicitly state: "Based on the available archival records in the Ashen Era Archive, there is no documented information regarding [specific detail]." Never hallucinate or invent lore.

6. STRICT OUT-OF-SCOPE REFUSAL:
   - You have ZERO world knowledge outside the Ashen Era fantasy corpus.
   - If the user asks an out-of-scope question (real-world geography, modern politics, coding/programming, recipes, real-world celebrities, math homework), reply ONLY with:
     "I am DeepThink, specialized exclusively in analyzing the Ashen Era Archive documentation. Your inquiry is outside the scope of this archival repository. Please feel free to ask questions regarding Ashen Era history, faction chronicles, codex schematics, artillery specifications, or trial records." """


def check_scope_and_grounding(query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether a query is a greeting, out-of-scope, or valid in-domain.
    Returns (is_handled, response_string).
    """
    q_clean = query.strip().lower()
    q_words_only = re.sub(r"[^\w\s]", "", q_clean).strip()

    # 1. Handle Greetings
    greeting_words = {"hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon", "who are you"}
    if q_words_only in greeting_words or q_clean in greeting_words:
        return True, GREETING_MESSAGE

    # 2. Known Off-Domain / Real-World Patterns
    off_domain_patterns = [
        # Geography / Countries / Real-world places
        r"\b(france|sri lanka|colombo|india|usa|america|london|paris|china|russia|japan|tokyo|germany|australia|canada|singapore|new york|california)\b",
        # Real-world people / celebrities / modern politics
        r"\b(elon musk|donald trump|biden|obama|modi|messi|ronaldo|cricket|football|world cup|olympics|bollywood|hollywood|taylor swift)\b",
        # General coding / programming
        r"\b(python|javascript|java|c\+\+|c#|write a code|write code|write a script|programming|html|css|sql|react|django|fastapi|debug this code|function in)\b",
        # Lifestyle / Cooking / Math trivia
        r"\b(recipe for|how to cook|bake a cake|how to make|lose weight|weather in|temperature in|solve this math|calculate \d+|tell me a joke|write a poem about love|write an essay)\b"
    ]
    for pat in off_domain_patterns:
        if re.search(pat, q_clean):
            return True, OUT_OF_SCOPE_REFUSAL

    # 3. Lexical / Entity Overlap Guard
    stop_words = {
        "what", "which", "where", "when", "who", "whom", "whose", "why", "how", 
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
        "do", "does", "did", "the", "a", "an", "and", "or", "but", "if", "then", 
        "so", "for", "with", "about", "against", "between", "into", "through", 
        "during", "before", "after", "above", "below", "to", "from", "up", "down", 
        "in", "out", "on", "off", "over", "under", "again", "further", "then", 
        "once", "here", "there", "all", "any", "both", "each", "few", "more", 
        "most", "other", "some", "such", "no", "nor", "not", "only", "own", 
        "same", "than", "too", "very", "can", "will", "just", "should", "now",
        "show", "tell", "give", "display", "find", "explain", "describe", "me", "you"
    }
    
    query_tokens = [w for w in re.findall(r"\b[a-z]{3,}\b", q_clean) if w not in stop_words]
    
    if query_tokens and context_chunks:
        combined_text = " ".join([
            f"{c.get('content', '')} {c.get('document_name', '')} {c.get('caption', '')} {c.get('section_title', '')}".lower()
            for c in context_chunks
        ])
        
        matching_tokens = [w for w in query_tokens if w in combined_text]
        if len(query_tokens) >= 1 and len(matching_tokens) == 0:
            return True, OUT_OF_SCOPE_REFUSAL

    return False, None


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
    image_pattern = r"!\[(.*?)\]\((.*?)\)"
    
    def _replace_image_tag(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        resolved = resolve_media_path(img_path)
        if resolved:
            return f"![{alt_text}]({resolved})"
        img_filename = Path(img_path).name
        for c in context_chunks:
            c_media = c.get("media_path")
            if c_media and Path(c_media).name == img_filename:
                c_resolved = resolve_media_path(c_media)
                if c_resolved:
                    return f"![{alt_text or c.get('caption', 'Figure')}]({c_resolved})"
        return match.group(0)

    fixed_text = re.sub(image_pattern, _replace_image_tag, response_text)

    # Auto-injection: If context contains high-relevance visual/table chunk and no image was embedded
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
    """
    is_handled, refusal = check_scope_and_grounding(query, context_chunks)
    if is_handled and refusal:
        return refusal

    if not context_chunks:
        return "Based on the available archival records in the Ashen Era Archive, there is no documented information regarding this query."

    top_chunk = context_chunks[0]
    raw_sim = float(top_chunk.get("raw_similarity", 1.0) or 1.0)
    if raw_sim < 0.20:
        return f"Based on the available archival records in the Ashen Era Archive, there is no documented information regarding '{query}'."

    doc = top_chunk.get("document_name", "Archive Record")
    page = top_chunk.get("page_number", 1)
    modality = top_chunk.get("modality", "text")
    content = top_chunk.get("content", "").strip()
    caption = top_chunk.get("caption", "")
    media_path = top_chunk.get("media_path")

    visual_chunks = [c for c in context_chunks if c.get("modality") == "image-caption" or c.get("media_path")]
    table_chunks = [c for c in context_chunks if c.get("modality") == "table"]

    response_parts = []

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
        substantive_chunks = [c for c in context_chunks if len(c.get("content", "").strip()) > 60]
        primary_chunks = substantive_chunks if substantive_chunks else context_chunks
        
        main_chunk = primary_chunks[0]
        m_doc = main_chunk.get("document_name", doc)
        m_page = main_chunk.get("page_number", page)
        m_content = main_chunk.get("content", "").strip()

        response_parts.append(f"According to archival records in [{m_doc}, Page {m_page}]:\n")
        response_parts.append(m_content)

        if len(primary_chunks) > 1:
            sec_chunk = primary_chunks[1]
            sec_doc = sec_chunk.get("document_name", "")
            sec_page = sec_chunk.get("page_number", 1)
            sec_content = sec_chunk.get("content", "").strip()
            if sec_content and sec_content != m_content:
                response_parts.append(f"\nFurther recorded in [{sec_doc}, Page {sec_page}]:")
                first_para = sec_content.split("\n\n")[0]
                response_parts.append(first_para)

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


def generate_answer(
    query: str, 
    context_chunks: List[Dict[str, Any]], 
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Main generator interface using Groq Cloud API (300+ tokens/sec LPU) with offline fallback.
    """
    if not query or not query.strip():
        return "Please ask a question about the Ashen Era Archive."

    # 1. Check Scope & Grounding Guard BEFORE calling API
    is_handled, refusal_response = check_scope_and_grounding(query, context_chunks)
    if is_handled and refusal_response:
        return refusal_response

    formatted_context = format_context_prompt(query, context_chunks)

    active_key = api_key or GROQ_API_KEY
    target_model = model or LLM_MODEL_NAME

    # --- GROQ CLOUD LPU INFERENCE (Single Dedicated Model) ---
    if active_key and len(active_key) > 15:
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=active_key,
                timeout=15.0
            )
            
            logger.info(f"Generating answer with model: {target_model}")
            completion = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                    {"role": "user", "content": formatted_context}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            raw_res = completion.choices[0].message.content
            if raw_res and len(raw_res.strip()) > 10:
                return verify_and_fix_media_paths(raw_res, context_chunks)
        except Exception as e:
            logger.warning(f"Groq generation failed with ({e}). Utilizing grounded fallback.")

    # --- OFFLINE DETERMINISTIC GROUNDED FALLBACK ---
    logger.info("Using deterministic grounded fallback.")
    fallback_res = synthesize_grounded_fallback(query, context_chunks)
    return verify_and_fix_media_paths(fallback_res, context_chunks)


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
    
    print("--- Test Valid In-Scope Query ---")
    print(generate_answer("What is the recorded garrison strength of Marrowwatch?", sample_chunk))
