"""
Query Intent Router (Owner: Member P3)
Analyzes user question to detect modality intent (visual diagram vs structured table vs text lore).
"""


def detect_modality_intent(query: str) -> str:
    """
    Returns 'image-caption', 'table', or 'text' based on query characteristics.
    """
    q_lower = query.lower()
    visual_keywords = ["diagram", "plate", "figure", "schematic", "map", "look like", "picture", "depicted", "illustration"]
    table_keywords = ["table", "specifications", "stats", "cost", "numbers", "matrix", "rows", "columns"]

    if any(k in q_lower for k in visual_keywords):
        return "image-caption"
    elif any(k in q_lower for k in table_keywords):
        return "table"
    return "text"
