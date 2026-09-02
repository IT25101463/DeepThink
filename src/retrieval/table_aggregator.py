"""
Structured Table & Quantitative Aggregator Module (RAG 3.0)
Parses Markdown tables, extracts numerical metrics (sums, calibers, troop numbers, budgets),
and synthesizes structured comparative matrices.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("deepthink.table_aggregator")


def parse_markdown_table(table_text: str) -> List[Dict[str, str]]:
    """
    Parses a markdown table string into a list of row dictionaries.
    """
    lines = [line.strip() for line in table_text.strip().split("\n") if line.strip()]
    if len(lines) < 3:
        return []

    # Filter out non-table lines
    table_lines = [l for l in lines if "|" in l]
    if len(table_lines) < 3:
        return []

    # Extract headers
    header_line = table_lines[0]
    headers = [h.strip() for h in header_line.split("|")[1:-1] if h.strip()]

    # Skip separator line (e.g., |---|---|)
    data_lines = table_lines[2:]

    rows = []
    for line in data_lines:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == len(headers):
            row_dict = {headers[i]: cells[i] for i in range(len(headers))}
            rows.append(row_dict)

    return rows


def aggregate_numeric_column(rows: List[Dict[str, str]], column_name: str) -> Dict[str, Any]:
    """
    Calculates sum, average, min, max, and count for a numerical column.
    """
    values = []
    for r in rows:
        val_str = r.get(column_name, "")
        # Extract first continuous number / float
        cleaned = re.sub(r"[^\d\.\-]", "", val_str)
        if cleaned:
            try:
                values.append(float(cleaned))
            except ValueError:
                pass

    if not values:
        return {"count": 0, "sum": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

    return {
        "count": len(values),
        "sum": round(sum(values), 2),
        "avg": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values)
    }


def extract_and_aggregate_tables(
    query: str,
    chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Scans retrieved chunks for table content, detects quantitative requests,
    and returns aggregated summaries and comparison tables.
    """
    table_chunks = [c for c in chunks if c.get("modality") == "table" or "|" in str(c.get("content", ""))]
    
    if not table_chunks:
        return {"has_tables": False, "tables_found": 0, "matrix_markdown": "", "aggregates": {}}

    all_parsed_rows = []
    matrix_lines = []

    for c in table_chunks:
        content = c.get("content", "")
        doc = c.get("document_name", "Archive Record")
        page = c.get("page_number", 1)
        
        parsed = parse_markdown_table(content)
        if parsed:
            all_parsed_rows.extend(parsed)
            matrix_lines.append(f"**Source: [{doc}, Page {page}]**\n{content}")

    # Look for aggregate keywords in query
    q_lower = query.lower()
    aggregates = {}
    
    if all_parsed_rows:
        sample_row = all_parsed_rows[0]
        numeric_cols = []
        for col, val in sample_row.items():
            if re.search(r"\d+", str(val)):
                numeric_cols.append(col)

        for col in numeric_cols:
            if any(k in q_lower for k in ("total", "sum", "average", "stats", "cost", "caliber", "garrison", "range")):
                aggregates[col] = aggregate_numeric_column(all_parsed_rows, col)

    return {
        "has_tables": True,
        "tables_found": len(table_chunks),
        "total_rows": len(all_parsed_rows),
        "matrix_markdown": "\n\n".join(matrix_lines),
        "aggregates": aggregates
    }
