"""
Document Parsing Module (Owner: Member P1)
Handles multi-format parsing of Markdown, DOCX, Plain Text, and standard/scanned PDF text.
Implements hierarchical, context-preserving chunking (~800 characters with ~150 character overlap)
and assigns rich metadata including source reliability ratings.
"""

import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.ingestion.ocr_engine import (
    is_scanned_page,
    process_scanned_pdf,
    run_ocr_on_image,
    init_tesseract,
)

logger = logging.getLogger(__name__)


def sanitize_id(text: str) -> str:
    """Creates a clean URL/filename-safe slug for chunk IDs."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9_]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text[:60] if text else "chunk"


def assign_source_reliability(file_path: Path) -> str:
    """
    Assigns domain reliability tier based on file path, folder, and document semantics:
    - official_codex: Authoritative world bibles and annals (high reliability).
    - wiki: Community/secondary lore articles.
    - novel: Narrative chronicles / storytelling accounts.
    - ephemera_trial: Court transcripts & military inquiries.
    - ephemera_tavern: Ballads, tavern tales, street poems (unreliable/embellished).
    - ephemera_ledger: Financial books, auction receipts, and trade contracts.
    - ephemera_letter: Personal and diplomatic correspondence.
    - ephemera_catalogue: Relic and auction catalogues.
    - ephemera: General in-world ephemera.
    """
    path_str = str(file_path).lower()
    name_str = file_path.stem.lower()

    if "codex" in path_str or "annals" in name_str or "codex_vaeloria" in name_str:
        return "official_codex"
    elif "wiki" in path_str:
        return "wiki"
    elif "chronicles" in path_str:
        return "novel"
    elif "trial" in name_str or "court_martial" in name_str:
        return "ephemera_trial"
    elif "ballad" in name_str or "tavern" in name_str or "song" in name_str:
        return "ephemera_tavern"
    elif "ledger" in name_str or "manifest" in name_str or "contract" in name_str:
        return "ephemera_ledger"
    elif "letter" in name_str or "correspondence" in name_str or "dispatch" in name_str:
        return "ephemera_letter"
    elif "catalogue" in name_str or "auction" in name_str:
        return "ephemera_catalogue"
    elif "ephemera" in path_str:
        return "ephemera"
    return "unknown"


def detect_document_type(file_path: Path) -> str:
    """
    Maps file extension to standard document_type enum:
    {"pdf", "docx", "md", "txt", "scan"}
    """
    name = file_path.name.lower()
    if ".scan.pdf" in name or "_scan" in name or "scan" in name:
        return "scan"
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    elif ext in [".md", ".markdown"]:
        return "md"
    elif ext == ".txt":
        return "txt"
    return "txt"


def hierarchical_chunk(
    text: str,
    doc_name: str,
    doc_type: str,
    page_num: int,
    section_title: str,
    base_metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Splits text into chunks (~800 characters with ~150 overlap), respecting
    paragraph, line, and sentence boundaries to avoid splitting mid-sentence.
    
    Generates standardized schema dictionary per chunk.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if base_metadata is None:
        base_metadata = {}

    chunks = []
    # If text is already shorter than target size + buffer, keep as single chunk
    if len(text) <= chunk_size + 100:
        raw_chunks = [text]
    else:
        raw_chunks = []
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len <= chunk_size:
                current_chunk.append(p)
                current_len += p_len + 2
            else:
                # If current chunk has content, commit it
                if current_chunk:
                    chunk_body = "\n\n".join(current_chunk)
                    raw_chunks.append(chunk_body)
                    
                    # Compute overlap text
                    overlap_chars = chunk_body[-chunk_overlap:] if len(chunk_body) > chunk_overlap else ""
                    current_chunk = [overlap_chars] if overlap_chars else []
                    current_len = len(overlap_chars)

                # If the single paragraph itself exceeds chunk_size, split by sentences
                if p_len > chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', p)
                    for sent in sentences:
                        sent = sent.strip()
                        if not sent:
                            continue
                        if current_len + len(sent) <= chunk_size:
                            current_chunk.append(sent)
                            current_len += len(sent) + 1
                        else:
                            if current_chunk:
                                raw_chunks.append(" ".join(current_chunk))
                                overlap_chars = " ".join(current_chunk)[-chunk_overlap:]
                                current_chunk = [overlap_chars] if overlap_chars else []
                                current_len = len(overlap_chars)
                            current_chunk.append(sent)
                            current_len += len(sent) + 1
                else:
                    current_chunk.append(p)
                    current_len += p_len + 2

        if current_chunk:
            rem = "\n\n".join(current_chunk).strip()
            if rem and (not raw_chunks or rem != raw_chunks[-1]):
                raw_chunks.append(rem)

    # Format into contract schema
    doc_stem = sanitize_id(Path(doc_name).stem)
    for idx, c_text in enumerate(raw_chunks):
        c_text = c_text.strip()
        if not c_text:
            continue
            
        chunk_id = f"{doc_stem}_p{page_num}_c{idx + 1:02d}"
        
        meta = dict(base_metadata)
        meta["word_count"] = len(c_text.split())
        meta["char_count"] = len(c_text)
        
        chunks.append({
            "chunk_id": chunk_id,
            "document_name": doc_name,
            "document_type": doc_type,
            "page_number": page_num,
            "section_title": section_title or Path(doc_name).stem.replace("_", " ").title(),
            "modality": "text",
            "content": c_text,
            "media_path": None,
            "caption": None,
            "metadata": meta
        })

    return chunks


def parse_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses a Markdown wiki/lore file into hierarchical section chunks by `#`, `##`, `###` headers.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        try:
            content = file_path.read_text(encoding="latin-1", errors="replace")
        except Exception as e2:
            logger.error(f"Failed to read markdown file {file_path}: {e2}")
            return []

    doc_name = file_path.name
    doc_type = "md"
    rel_tag = assign_source_reliability(file_path)
    base_meta = {
        "source_reliability": rel_tag,
        "source_category": "wiki",
        "file_path": str(file_path.name)
    }

    chunks = []
    lines = content.splitlines()
    
    current_headers = {}  # level -> title
    current_section_title = file_path.stem.replace("_", " ").title()
    current_section_lines = []
    page_num = 1

    def flush_section(sec_title: str, sec_lines: List[str]):
        sec_text = "\n".join(sec_lines).strip()
        if sec_text:
            return hierarchical_chunk(
                text=sec_text,
                doc_name=doc_name,
                doc_type=doc_type,
                page_num=page_num,
                section_title=sec_title,
                base_metadata=base_meta
            )
        return []

    for line in lines:
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            # Flush accumulated text
            if current_section_lines:
                chunks.extend(flush_section(current_section_title, current_section_lines))
                current_section_lines = []
            
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            # Update header hierarchy
            current_headers[level] = title
            # Remove deeper headers from previous sections
            current_headers = {k: v for k, v in current_headers.items() if k <= level}
            
            # Build compound section title: "Wiki > History > Early Era"
            sorted_levels = sorted(current_headers.keys())
            current_section_title = " > ".join(current_headers[lvl] for lvl in sorted_levels)
        else:
            current_section_lines.append(line)

    if current_section_lines:
        chunks.extend(flush_section(current_section_title, current_section_lines))

    # Fallback if no header chunks created
    if not chunks and content.strip():
        chunks.extend(hierarchical_chunk(
            text=content.strip(),
            doc_name=doc_name,
            doc_type=doc_type,
            page_num=1,
            section_title=current_section_title,
            base_metadata=base_meta
        ))

    return chunks


def parse_docx_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses a DOCX document into paragraphs and table text, tracking heading styles.
    """
    try:
        import docx
    except ImportError:
        logger.error("python-docx is required to parse DOCX files.")
        return []

    doc_name = file_path.name
    doc_type = "docx"
    rel_tag = assign_source_reliability(file_path)
    base_meta = {
        "source_reliability": rel_tag,
        "source_category": "chronicles" if "chronicles" in str(file_path).lower() else "codex" if "codex" in str(file_path).lower() else "ephemera",
        "file_path": str(file_path.name)
    }

    try:
        doc = docx.Document(str(file_path))
    except Exception as e:
        logger.error(f"Failed to open DOCX {file_path}: {e}")
        return []

    chunks = []
    current_section_title = file_path.stem.replace("_", " ").title()
    current_lines = []
    page_estimate = 1
    char_counter = 0

    def flush_docx_section():
        nonlocal current_lines, page_estimate
        if not current_lines:
            return []
        text_block = "\n".join(current_lines).strip()
        current_lines = []
        if not text_block:
            return []
        return hierarchical_chunk(
            text=text_block,
            doc_name=doc_name,
            doc_type=doc_type,
            page_num=page_estimate,
            section_title=current_section_title,
            base_metadata=base_meta
        )

    for p in doc.paragraphs:
        p_text = p.text.strip()
        if not p_text:
            continue

        style_name = p.style.name.lower() if p.style and p.style.name else ""
        if "heading" in style_name or "title" in style_name:
            chunks.extend(flush_docx_section())
            current_section_title = f"{file_path.stem.replace('_', ' ').title()} > {p_text}"
        else:
            current_lines.append(p_text)
            char_counter += len(p_text)
            # Estimate standard page boundaries (~2500 characters per page)
            if char_counter >= 2500:
                chunks.extend(flush_docx_section())
                page_estimate += 1
                char_counter = 0

    # Also extract text from tables in DOCX
    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells]
            if any(row_cells):
                table_rows.append(" | ".join(row_cells))
        if table_rows:
            table_text = "\n".join(table_rows)
            current_lines.append(table_text)
            char_counter += len(table_text)

    chunks.extend(flush_docx_section())

    return chunks


def parse_pdf_text(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extracts text from a PDF file page by page using PyMuPDF (fitz).
    Detects scanned pages and routes them to OCR if needed.
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            logger.error("PyMuPDF is required to parse PDF files.")
            return []

    doc_name = file_path.name
    doc_type = detect_document_type(file_path)
    rel_tag = assign_source_reliability(file_path)
    base_meta = {
        "source_reliability": rel_tag,
        "source_category": "chronicles" if "chronicles" in str(file_path).lower() else "codex" if "codex" in str(file_path).lower() else "ephemera",
        "file_path": str(file_path.name)
    }

    chunks = []
    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        logger.error(f"Failed to open PDF {file_path}: {e}")
        return []

    current_section_title = file_path.stem.replace("_", " ").title()

    tesseract_available = init_tesseract()

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        
        # Check if page is scanned/image-only AND OCR is available
        if tesseract_available and (is_scanned_page(page) or doc_type == "scan"):
            pix = page.get_pixmap(dpi=150)
            from PIL import Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = run_ocr_on_image(img, preprocess=True)
            page_text = ocr_text if ocr_text.strip() else page.get_text("text").strip()
            is_ocr = True
        else:
            page_text = page.get_text("text").strip()
            is_ocr = False

        if not page_text:
            continue

        # Look for possible top-level section header on the page
        lines = page_text.splitlines()
        if lines:
            first_line = lines[0].strip()
            if len(first_line) > 3 and len(first_line) < 80 and not first_line.endswith("."):
                current_section_title = f"{file_path.stem.replace('_', ' ').title()} > {first_line}"

        page_meta = dict(base_meta)
        page_meta["is_ocr"] = is_ocr

        page_chunks = hierarchical_chunk(
            text=page_text,
            doc_name=doc_name,
            doc_type=doc_type,
            page_num=page_num,
            section_title=current_section_title,
            base_metadata=page_meta
        )
        chunks.extend(page_chunks)

    doc.close()
    return chunks


def parse_txt_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses a plain text file into structured chunks.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        try:
            content = file_path.read_text(encoding="latin-1", errors="replace")
        except Exception as e2:
            logger.error(f"Failed to read TXT file {file_path}: {e2}")
            return []

    doc_name = file_path.name
    doc_type = "txt"
    rel_tag = assign_source_reliability(file_path)
    base_meta = {
        "source_reliability": rel_tag,
        "source_category": "ephemera",
        "file_path": str(file_path.name)
    }

    section_title = file_path.stem.replace("_", " ").title()
    lines = content.splitlines()
    if lines:
        for l in lines[:5]:
            l_strip = l.strip()
            if l_strip.isupper() and len(l_strip) > 3 and len(l_strip) < 70:
                section_title = f"{file_path.stem.replace('_', ' ').title()} > {l_strip}"
                break

    return hierarchical_chunk(
        text=content,
        doc_name=doc_name,
        doc_type=doc_type,
        page_num=1,
        section_title=section_title,
        base_metadata=base_meta
    )


def parse_document(file_path: Path) -> List[Dict[str, Any]]:
    """
    Universal dispatcher: parses a single file (PDF/DOCX/MD/TXT/Scan)
    and returns schema-compliant structured text chunks.
    """
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"File not found: {file_path}")
        return []

    try:
        suffix = file_path.suffix.lower()
        if suffix in [".md", ".markdown"]:
            return parse_markdown_file(file_path)
        elif suffix == ".docx":
            return parse_docx_file(file_path)
        elif suffix == ".pdf":
            return parse_pdf_text(file_path)
        elif suffix == ".txt":
            return parse_txt_file(file_path)
        else:
            logger.debug(f"Skipping unsupported file type: {file_path}")
            return []
    except Exception as e:
        logger.error(f"Error parsing document {file_path.name}: {e}")
        return []
