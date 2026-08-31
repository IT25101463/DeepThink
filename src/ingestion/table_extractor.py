"""
Table Extraction Module (Owner: Member P2)
Extracts tabular data from PDFs and formats them into clean Markdown tables with rich metadata.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from src.ingestion.parser import assign_source_reliability, sanitize_id

logger = logging.getLogger(__name__)


def format_markdown_table(table_data: List[List[Any]]) -> str:
    """
    Converts a 2D grid/list of table cells into a clean, GitHub-flavored Markdown table.
    Cleans up newlines, escapes pipe symbols, and normalizes column counts.
    """
    if not table_data or len(table_data) == 0:
        return ""

    cleaned_rows = []
    for row in table_data:
        if row is None:
            continue
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                c = str(cell).replace("\r\n", " ").replace("\n", " ").strip()
                c = re.sub(r'\s+', ' ', c)
                c = c.replace("|", "\\|")
                cleaned_row.append(c)
        # Filter out rows that are entirely empty
        if any(c for c in cleaned_row):
            cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return ""

    max_cols = max(len(r) for r in cleaned_rows)
    if max_cols == 0:
        return ""

    # Ensure all rows have uniform column count
    for r in cleaned_rows:
        while len(r) < max_cols:
            r.append("")

    if len(cleaned_rows) == 1:
        # Single row table (key-value or headerless)
        header = ["Property", "Record"] if max_cols == 2 else [f"Col {i+1}" for i in range(max_cols)]
        separator = ["---"] * max_cols
        data_rows = cleaned_rows
    else:
        header = cleaned_rows[0]
        separator = ["---"] * max_cols
        data_rows = cleaned_rows[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |"
    ]
    for r in data_rows:
        lines.append("| " + " | ".join(r) + " |")

    return "\n".join(lines)


def extract_tables_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extracts structured tables from a PDF using pdfplumber, converting each table
    into a standardized 'table' chunk with Markdown content.
    """
    if pdfplumber is None:
        logger.warning("pdfplumber is not installed; skipping PDF table extraction.")
        return []

    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return []

    # Skip scan-only documents where tables cannot be extracted via text plumber
    if ".scan." in pdf_path.name.lower() or "_scan" in pdf_path.name.lower():
        logger.debug(f"Skipping table extraction for scanned PDF: {pdf_path.name}")
        return []

    doc_stem = sanitize_id(pdf_path.stem)
    rel_tag = assign_source_reliability(pdf_path)
    chunks = []

    try:
        with pdfplumber.open(pdf_path) as plum:
            for page_idx, page in enumerate(plum.pages):
                page_num = page_idx + 1
                try:
                    tables = page.extract_tables()
                except Exception as e:
                    logger.debug(f"Error extracting tables on page {page_num} of {pdf_path.name}: {e}")
                    continue

                if not tables:
                    continue

                # Extract page text to get section context
                page_text = page.extract_text() or ""
                lines = [l.strip() for l in page_text.splitlines() if l.strip()]
                section_title = pdf_path.stem.replace("_", " ").title()
                for line in lines[:3]:
                    if len(line) > 3 and not line.startswith("Plate") and not line.endswith("."):
                        section_title = f"{pdf_path.stem.replace('_', ' ').title()} > {line}"
                        break

                for t_idx, table_data in enumerate(tables):
                    md_table = format_markdown_table(table_data)
                    if not md_table.strip():
                        continue

                    chunk_id = f"{doc_stem}_p{page_num:02d}_tab{t_idx + 1:02d}"
                    row_count = len(table_data)
                    col_count = max((len(r) for r in table_data), default=0)

                    # Extract primary entities from table content
                    entities = [pdf_path.stem.replace("_", " ").title()]
                    if len(table_data) > 0 and table_data[0]:
                        entities.extend([str(c).strip() for c in table_data[0] if c and len(str(c).strip()) < 40])

                    caption = f"Data Table: {section_title} (Page {page_num}, Table {t_idx + 1})"

                    chunks.append({
                        "chunk_id": chunk_id,
                        "document_name": pdf_path.name,
                        "document_type": "pdf",
                        "page_number": page_num,
                        "section_title": section_title,
                        "modality": "table",
                        "content": md_table,
                        "media_path": None,
                        "caption": caption,
                        "metadata": {
                            "table_dimensions": [row_count, col_count],
                            "source_reliability": rel_tag,
                            "source_category": "codex" if "codex" in str(pdf_path).lower() else "ephemera",
                            "related_entities": list(set(entities))[:5],
                            "file_path": pdf_path.name
                        }
                    })

    except Exception as e:
        logger.error(f"Failed to open or process tables in {pdf_path.name}: {e}")

    return chunks

