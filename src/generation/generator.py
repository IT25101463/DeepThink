"""
Grounded Generation Engine (Owner: Member P4 - Generation, Evaluation & Delivery Lead)
Calls Groq Cloud API (300+ tokens/sec LPU inference), enforces citations, embeds media links,
handles Corrective RAG (CRAG) confidence grading, and enforces domain guardrails for out-of-scope queries.
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.config import (
    GROQ_API_KEY,
    LLM_MODEL_NAME, 
    PROJECT_ROOT, 
    EXTRACTED_MEDIA_DIR
)
from src.retrieval.router import check_query_domain_scope

logger = logging.getLogger("deepthink.generator")

# Strict Grounded Scholarly System Prompt for Sub-track 1A (High Intelligence, User-Friendly & Specificity)
GROUNDED_SYSTEM_PROMPT = """You are DeepThink, the master archival intelligence and senior scholar of the Ashen Era Archive.
You provide deeply intelligent, comprehensive, beautifully structured, and user-friendly analyses of archival documentation using ONLY the retrieved context chunks provided below.

CORE OPERATING DIRECTIVES:

1. INTELLIGENCE, DEPTH & SPECIFICITY (SCHOLARLY RIGOR):
   - Provide thorough, intellectually rigorous, and complete explanations. Never provide shallow, lazy, or one-sentence summaries.
   - Synthesize all relevant facts across ALL provided context chunks into a coherent, structured, and nuanced narrative.
   - Always extract and highlight exact proper names, honorific titles, dates, geographical regions, troop strengths, battle casualty numbers, artifact specifications, ledger sums, and architectural dimensions whenever present in the context.
   - Structure your response cleanly for the user:
     * **Executive Summary**: 1-2 sentence core direct answer upfront.
     * **Detailed Archival Breakdown**: Thematic bullet points with bold headers (e.g. History, Technical Specs, Personnel).
     * **Multimodal Assets**: Rendered tables or embedded figure plates where applicable.
     * **Key Takeaway**: A concise concluding synthesis.

2. ZERO FLUFF & DIRECT USER-FRIENDLY TONE:
   - Speak with the authoritative, engaging, and articulate voice of an elite historical archivist.
   - Avoid generic conversational filler such as "Based on the text provided...", "Sure, I can help with that...", or "Here is what I found...".
   - Start immediately with the core truth and substantive explanation.

3. PRECISE IN-TEXT CITATIONS:
   - Every factual claim, statistic, entity mention, or historical assertion MUST be immediately substantiated with an exact bracket citation:
     [Document Name, Page X].
   - If multiple documents corroborate a fact, cite all relevant sources: [Doc1, Page X; Doc2, Page Y].

4. SUB-TRACK 1A: MULTIMODAL INLINE FIGURE & TABLE EMBEDDINGS:
   - When a retrieved chunk contains a visual figure plate or table with a valid `media_path`, you MUST embed the figure directly into your response:
     ![Descriptive Caption](media_path)
   - Accompany every embedded figure with explanatory analysis explaining what the visual plate depicts according to archival records.
   - Format tabular data in clean, readable GitHub Markdown tables.

5. SOURCE CONFLICT RESOLUTION & STRICT NON-EXTRAPOLATION (EPISTEMIC RESTRAINT):
   - When archival records present a discrepancy, contradiction, or omission (e.g., one document names a faction as victor while another lists it only as a belligerent), state BOTH records exactly as written.
   - DO NOT invent or speculate on unverified reasons for the discrepancy (e.g., do NOT speculate about "divergent narrative framing", "author motives", or link unrelated secret events as causes for document omissions).
   - Explicitly state that the archive presents both entries as distinct facts and provides NO explicit reconciliation between them.
   - Never extrapolate geographical, military, or biographical facts beyond the text (e.g., if a conflict was waged at multiple locations, do NOT assume a faction fought at every site unless explicitly stated).
   - Accurately distinguish source types (wiki entries, contemporary letters, official codices) without exaggerating authority.
   - If a specific detail is unrecorded, state plainly: "Based on the available records in the Ashen Era Archive, there is no documented information regarding [specific detail]."

6. STRICT OUT-OF-SCOPE REFUSAL:
   - You have ZERO world knowledge outside the Ashen Era fantasy corpus.
   - If the user asks an out-of-scope question (real-world geography, modern politics, coding/programming, recipes, real-world celebrities, math homework), reply ONLY with:
     "I am DeepThink, specialized exclusively in analyzing the Ashen Era Archive documentation. Your inquiry is outside the scope of this archival repository. Please feel free to ask questions regarding Ashen Era history, faction chronicles, codex schematics, artillery specifications, or trial records." """


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
        # Budget chunk content to prevent runaway token usage on free tier TPM limits
        trimmed_content = content.strip()
        if len(trimmed_content) > 1200:
            trimmed_content = trimmed_content[:1200] + "... [archival snippet trimmed for context budget]"
        context_lines.append(f"Content:\n{trimmed_content}")

    # RAG 3.0: Quantitative Aggregates Integration
    from src.retrieval.table_aggregator import extract_and_aggregate_tables
    tbl_data = extract_and_aggregate_tables(query, chunks)
    if tbl_data.get("aggregates"):
        context_lines.append("\n--- [Computed Quantitative Aggregates] ---")
        for col, stats in tbl_data["aggregates"].items():
            context_lines.append(f"- Metric '{col}': Total Sum = {stats['sum']}, Average = {stats['avg']}, Count = {stats['count']}")

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


def normalize_citations(response_text: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Convert model shorthand citations into verified document/page citations."""
    if not response_text or not context_chunks:
        return response_text

    chunk_citation = re.compile(
        r"(?:\[|【)\s*Chunk\s*(\d+)\s*(?:,\s*Page\s*(\d+))?\s*(?:\]|】)",
        flags=re.IGNORECASE,
    )

    def replace_chunk(match: re.Match[str]) -> str:
        chunk_index = int(match.group(1)) - 1
        if not 0 <= chunk_index < len(context_chunks):
            return match.group(0)
        chunk = context_chunks[chunk_index]
        document = chunk.get("document_name", "Archive Record")
        page = match.group(2) or chunk.get("page_number", 1)
        return f"[{document}, Page {page}]"

    normalized = chunk_citation.sub(replace_chunk, response_text)
    normalized = re.sub(
        r"\[Document:\s*([^,\]]+),\s*Page\s*(\d+)\]",
        r"[\1, Page \2]",
        normalized,
        flags=re.IGNORECASE,
    )
    # Models may emit typographic non-breaking spaces in measurements and
    # citations; normalize them so UI text and downstream checks are stable.
    normalized = normalized.replace("\u202f", " ").replace("\u00a0", " ")

    known_documents = [str(c.get("document_name", "")) for c in context_chunks]
    has_verified_citation = any(
        document and f"[{document}, Page" in normalized
        for document in known_documents
    )
    if not has_verified_citation:
        source = context_chunks[0]
        document = source.get("document_name", "Archive Record")
        page = source.get("page_number", 1)
        normalized = normalized.rstrip() + f"\n\nSource: [{document}, Page {page}]"

    return normalized


def synthesize_grounded_fallback(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Deterministic offline context synthesizer that generates grounded,
    hallucination-free answers with precise citations and media embeds directly from retrieved chunks.
    """
    if not context_chunks:
        return f"Based on the available archival records in the Ashen Era Archive, there is no documented information regarding '{query}'."

    top_chunk = context_chunks[0]
    raw_sim = float(top_chunk.get("raw_similarity", 1.0) or 1.0)
    if raw_sim < 0.25:
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

    # 1. Executive Summary & Core Archival Findings
    if visual_chunks:
        v_chunk = visual_chunks[0]
        v_doc = v_chunk.get("document_name", doc)
        v_page = v_chunk.get("page_number", page)
        v_caption = v_chunk.get("caption") or v_chunk.get("content", "")
        v_media = v_chunk.get("media_path")
        resolved_media = resolve_media_path(v_media) if v_media else None
        
        response_parts.append(f"### Archival Record Overview\nAccording to official documentation in [{v_doc}, Page {v_page}]:\n")
        response_parts.append(f"{v_chunk.get('content', '')}")
        
        if resolved_media:
            caption_clean = v_caption if v_caption else "Official Archive Figure Plate"
            display_title = re.sub(r"^(figure plate|figure|plate):\s*", "", caption_clean, flags=re.IGNORECASE).strip()
            response_parts.append(f"\n\n![{caption_clean}]({resolved_media})")
            response_parts.append(f"\n*Figure Plate: {display_title} — Source: [{v_doc}, Page {v_page}]*")

    elif table_chunks:
        t_chunk = table_chunks[0]
        t_doc = t_chunk.get("document_name", doc)
        t_page = t_chunk.get("page_number", page)
        response_parts.append(f"### Structured Archival Ledger\nAccording to records in [{t_doc}, Page {t_page}]:\n")
        response_parts.append(t_chunk.get("content", ""))
        
    else:
        substantive_chunks = [c for c in context_chunks if len(c.get("content", "").strip()) > 60]
        primary_chunks = substantive_chunks if substantive_chunks else context_chunks
        
        main_chunk = primary_chunks[0]
        m_doc = main_chunk.get("document_name", doc)
        m_page = main_chunk.get("page_number", page)
        m_content = main_chunk.get("content", "").strip()

        response_parts.append(f"### Archival Synthesis\nAccording to historical records in [{m_doc}, Page {m_page}]:\n")
        response_parts.append(m_content)

        if len(primary_chunks) > 1:
            sec_chunk = primary_chunks[1]
            sec_doc = sec_chunk.get("document_name", "")
            sec_page = sec_chunk.get("page_number", 1)
            sec_content = sec_chunk.get("content", "").strip()
            if sec_content and sec_content != m_content:
                response_parts.append(f"\n\n### Corroborating Archival Details\nFurther recorded in [{sec_doc}, Page {sec_page}]:")
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

    # RAG 3.0: Quantitative Table Summary
    from src.retrieval.table_aggregator import extract_and_aggregate_tables
    tbl_data = extract_and_aggregate_tables(query, context_chunks)
    if tbl_data.get("aggregates"):
        agg_lines = ["\n\n**Quantitative Table Analysis:**"]
        for col, stats in tbl_data["aggregates"].items():
            agg_lines.append(f"- **{col.title()} Total**: Sum = `{stats['sum']}`, Average = `{stats['avg']}` (across {stats['count']} records)")
        response_parts.append("\n".join(agg_lines))

    return "\n".join(response_parts)


def generate_answer(
    query: str, 
    context_chunks: List[Dict[str, Any]], 
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Main generator interface using Groq Cloud API (300+ tokens/sec LPU) with CRAG confidence grading.
    """
    if not query or not query.strip():
        return "Please ask a question about the Ashen Era Archive."

    # 1. Check Scope & Physical Premise Guard BEFORE calling API
    is_handled, refusal_response, _ = check_query_domain_scope(query)
    if is_handled and refusal_response:
        return refusal_response

    from src.retrieval.router import UNIVERSAL_OOD_REFUSAL

    if not context_chunks:
        return UNIVERSAL_OOD_REFUSAL

    # 2. Universal Corrective RAG (CRAG) & OOD Confidence Check
    from src.retrieval.retriever import evaluate_retrieval_confidence
    crag_eval = evaluate_retrieval_confidence(query, context_chunks)
    if crag_eval["verdict"] == "OUT_OF_DOMAIN" or not crag_eval.get("is_in_domain", True):
        return UNIVERSAL_OOD_REFUSAL

    # 3. Pre-Generation Context Verification & Distractor Pruning Gate
    from src.retrieval.verifier import verify_and_filter_context
    clean_chunks, v_report = verify_and_filter_context(query, context_chunks)
    if not v_report.get("is_sufficient", True) or not clean_chunks:
        return f"Based on the available records in the Ashen Era Archive, there is no documented information regarding '{query}'."

    active_chunks = clean_chunks
    formatted_context = format_context_prompt(query, active_chunks)

    active_key = api_key or GROQ_API_KEY
    target_model = model or LLM_MODEL_NAME

    # --- INFERENCE API CALL (Groq Cloud LPU or OpenRouter) ---
    if active_key and len(active_key) > 15:
        try:
            from openai import OpenAI
            
            # Auto-detect OpenRouter vs Groq
            if active_key.startswith("sk-or-"):
                api_base = "https://openrouter.ai/api/v1"
                if not target_model or "versatile" in target_model:
                    target_model = "meta-llama/llama-3.3-70b-instruct:free"
            else:
                api_base = "https://api.groq.com/openai/v1"
                # Normalize Groq model ID
                if ":free" in target_model or "meta-llama/" in target_model:
                    target_model = "llama-3.3-70b-versatile"
                elif "120b" in target_model.lower():
                    target_model = "openai/gpt-oss-120b"
                elif re.search(r"(?<!1)20b", target_model.lower()):
                    target_model = "openai/gpt-oss-20b"
                elif "qwen" in target_model.lower():
                    target_model = "qwen/qwen3.8-27b"
                elif not target_model:
                    target_model = "openai/gpt-oss-120b"

            client = OpenAI(
                base_url=api_base,
                api_key=active_key,
                timeout=15.0
            )
            
            logger.info(f"Generating answer via {api_base} with model: {target_model}")
            for attempt in range(3):
                try:
                    completion = client.chat.completions.create(
                        model=target_model,
                        messages=[
                            {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                            {"role": "user", "content": formatted_context}
                        ],
                        temperature=0.1,
                        max_tokens=800
                    )
                    raw_res = completion.choices[0].message.content
                    if raw_res and len(raw_res.strip()) > 10:
                        normalized = normalize_citations(raw_res, active_chunks)
                        return verify_and_fix_media_paths(normalized, active_chunks)
                    raise RuntimeError("LLM returned an empty or very short response")
                except Exception as e:
                    err_str = str(e)
                    if attempt == 2:
                        logger.warning(f"Generation API failed after 3 attempts ({err_str}). Utilizing grounded fallback.")
                    else:
                        # Extract precise backoff wait time if rate limited (e.g. 'try again in 6.81s')
                        wait_match = re.search(r"try again in ([\d\.]+)s", err_str, re.IGNORECASE)
                        if wait_match:
                            delay = min(float(wait_match.group(1)) + 0.6, 12.0)
                        else:
                            delay = 2 ** (attempt + 1)

                        # If rate limited (HTTP 429) on Groq, fallback to high-TPM model for next attempt
                        if ("429" in err_str or "rate limit" in err_str.lower()) and "groq" in api_base:
                            if "gpt-oss" in target_model:
                                target_model = "llama-3.3-70b-versatile"
                                logger.info(f"Rate limit encountered. Switching model to: {target_model}")
                            elif "llama-3.3" in target_model:
                                target_model = "llama-3.1-8b-instant"
                                logger.info(f"Rate limit encountered. Switching model to: {target_model}")

                        logger.warning(f"Generation API attempt {attempt + 1} failed ({err_str}); retrying in {delay:.1f}s.")
                        time.sleep(delay)
        except Exception as e:
            logger.warning(f"Generation client setup failed with ({e}). Utilizing grounded fallback.")

    # --- OFFLINE DETERMINISTIC GROUNDED FALLBACK ---
    logger.info("Using deterministic grounded fallback.")
    fallback_res = synthesize_grounded_fallback(query, active_chunks)
    normalized = normalize_citations(fallback_res, active_chunks)
    return verify_and_fix_media_paths(normalized, active_chunks)


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
