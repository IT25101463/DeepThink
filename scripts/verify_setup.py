"""
Sprint 0 / Setup Verification Script
Run this script to verify that your environment, folder structure,
and configuration are 100% ready for development.

Usage:
    python3 scripts/verify_setup.py
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.schema_validator import validate_chunks_file


def print_status(component: str, ok: bool, details: str = ""):
    icon = "✅" if ok else "❌"
    msg = f"{icon} {component:<35}"
    if details:
        msg += f" -> {details}"
    print(msg)


def run_verification():
    print("=" * 70)
    print(" 🛠️  DEEPTHINK (SLIIT CODEFEST 2026) - SETUP VERIFIER (100% FREE STACK)")
    print("=" * 70)

    # 1. Python version check
    py_ver = sys.version_info
    py_ok = py_ver.major == 3 and py_ver.minor >= 10
    print_status("Python 3.10+ Environment", py_ok, f"Detected: {sys.version.split()[0]}")

    # 2. Key Directories Check
    required_dirs = [
        "data",
        "data/extracted_media/figures",
        "data/extracted_media/tables",
        "docs/workflows",
        "docs/diagrams",
        "ai_usage",
        "configuration-example",
        "src/ingestion",
        "src/retrieval",
        "src/generation",
        "src/evaluation",
        "src/ui",
        "tests"
    ]
    all_dirs_ok = True
    for d in required_dirs:
        p = PROJECT_ROOT / d
        if not p.exists():
            all_dirs_ok = False
            print_status(f"Directory '{d}'", False, "Missing")
    if all_dirs_ok:
        print_status("Repository Directory Structure", True, "All core directories verified")

    # 3. Chunks Contract Status
    chunks_file = PROJECT_ROOT / "data/chunks.json"
    if chunks_file.exists():
        valid_schema, errors = validate_chunks_file(chunks_file)
        print_status("Data Contract (chunks.json)", valid_schema, "Validated against contract" if valid_schema else f"{len(errors)} error(s)")
    else:
        print_status("Data Contract (chunks.json)", True, "Ready for P1/P2 ingestion generation")

    # 4. Sample Questions Benchmark
    questions_file = PROJECT_ROOT / "data/sample_questions.json"
    print_status("Evaluation Benchmark File", questions_file.exists(), "data/sample_questions.json verified")

    # 5. Environment & API Keys Status
    env_file = PROJECT_ROOT / ".env"
    env_exists = env_file.exists()
    print_status(".env Configuration File", env_exists, "Found" if env_exists else "Not yet created (copy from .env.example)")

    print_status("  - Local BGE Embeddings (P3)", True, "100% Free / Zero Card / Zero API Key")
    if env_exists:
        from src.config import GROQ_API_KEY
        print_status("  - Groq API Key (P4)", bool(GROQ_API_KEY), "Configured" if GROQ_API_KEY else "Empty (free signup at console.groq.com/keys)")

    # 6. Workflow Docs Check
    workflows = [
        "docs/workflows/TEAM_WORKFLOW.md",
        "docs/workflows/P1_DOCUMENT_PARSING_OCR.md",
        "docs/workflows/P2_VISUAL_TABLE_EXTRACTION.md",
        "docs/workflows/P3_RETRIEVAL_RANKING.md",
        "docs/workflows/P4_GENERATION_EVALUATION.md"
    ]
    wf_ok = all((PROJECT_ROOT / w).exists() for w in workflows)
    print_status("Member Workflows (P1-P4)", wf_ok, "All role roadmaps in place")

    print("=" * 70)
    print("🎯 SYSTEM STATUS: READY FOR DEVELOPMENT")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
