"""
Schema Validator for data/chunks.json
Ensures strict compliance with the Sub-track 1A data contract across all 4 team roles.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

VALID_MODALITIES = {"text", "table", "image-caption"}
VALID_DOC_TYPES = {"pdf", "docx", "md", "txt", "scan"}


def validate_chunk(chunk: Dict[str, Any], project_root: Path) -> List[str]:
    """
    Validates a single chunk dictionary against contract requirements.
    Returns a list of error strings (empty if valid).
    """
    errors = []
    
    # Required keys check
    required_keys = ["chunk_id", "document_name", "document_type", "page_number", "section_title", "modality", "content"]
    for k in required_keys:
        if k not in chunk or chunk[k] is None:
            errors.append(f"Missing or null required key: '{k}'")
            
    # Modality validation
    modality = chunk.get("modality")
    if modality not in VALID_MODALITIES:
        errors.append(f"Invalid modality '{modality}'. Must be one of {VALID_MODALITIES}")
        
    # Doc type validation
    doc_type = chunk.get("document_type")
    if doc_type not in VALID_DOC_TYPES:
        errors.append(f"Invalid document_type '{doc_type}'. Must be one of {VALID_DOC_TYPES}")
        
    # Media path validation for visual/table chunks
    media_path = chunk.get("media_path")
    if modality in {"image-caption", "table"} and media_path:
        full_path = project_root / media_path
        if not full_path.exists():
            errors.append(f"Media file does not exist on disk: '{media_path}' (Resolved: {full_path})")
            
    # Content check
    content = chunk.get("content", "")
    if not isinstance(content, str) or len(content.strip()) == 0:
        errors.append("Content field must be a non-empty string.")
        
    return errors


def validate_chunks_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates an entire chunks.json file.
    Returns (is_valid, error_list).
    """
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"Failed to parse JSON file: {e}"]
        
    if not isinstance(data, list):
        return False, ["Root JSON structure must be a list of chunk objects."]
        
    if len(data) == 0:
        return False, ["Chunks list is empty."]
        
    project_root = file_path.resolve().parent.parent
    all_errors = []
    
    seen_ids = set()
    for idx, chunk in enumerate(data):
        if not isinstance(chunk, dict):
            all_errors.append(f"Chunk at index {idx} is not an object.")
            continue
            
        c_id = chunk.get("chunk_id")
        if c_id in seen_ids:
            all_errors.append(f"Duplicate chunk_id detected: '{c_id}' at index {idx}")
        elif c_id:
            seen_ids.add(c_id)
            
        chunk_errs = validate_chunk(chunk, project_root)
        for err in chunk_errs:
            all_errors.append(f"Chunk [{c_id or idx}]: {err}")
            
    return len(all_errors) == 0, all_errors


if __name__ == "__main__":
    import sys
    target = Path("data/chunks.json")
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        
    valid, errs = validate_chunks_file(target)
    if valid:
        print(f"✅ SUCCESS: '{target}' passed all schema contract validation checks.")
    else:
        print(f"❌ FAILED: '{target}' has {len(errs)} schema error(s):")
        for e in errs[:10]:
            print(f"  - {e}")
        if len(errs) > 10:
            print(f"  ... and {len(errs) - 10} more errors.")
        sys.exit(1)
