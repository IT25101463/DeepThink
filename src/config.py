"""
Global configuration loader for DeepThink.
Loads environment variables from .env and settings from configuration-example/config.example.json.
100% Free & Local-First Architecture (Zero Credit Cards, Zero Secret Leaks).
"""

import os
from pathlib import Path

# Windows SSL root certificates injector
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Graceful dotenv loader
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# API Keys (Groq is 100% free with ultra-fast 300 t/s LPU inference & zero credit card needed)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Model Names (Defaults to Groq Flagship GPT-OSS 120B / 20B)
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "openai/gpt-oss-120b")
# 100% free local HuggingFace embedding (Zero card / Zero API key needed)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
CORPUS_DIR = PROJECT_ROOT / os.getenv("ASSET_CORPUS_DIR", "data/Ashen_Era_Archive")
EXTRACTED_MEDIA_DIR = PROJECT_ROOT / os.getenv("EXTRACTED_MEDIA_DIR", "data/extracted_media")
CHUNKS_JSON_PATH = PROJECT_ROOT / os.getenv("CHUNKS_JSON_PATH", "data/chunks.json")
CHROMA_PERSIST_DIR = PROJECT_ROOT / os.getenv("CHROMA_PERSIST_DIR", "chroma_db")

# Retrieval Parameters
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
MODALITY_BOOST_FACTOR = float(os.getenv("MODALITY_BOOST_FACTOR", "1.5"))

# Ensure essential output directories exist
EXTRACTED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
(EXTRACTED_MEDIA_DIR / "figures").mkdir(parents=True, exist_ok=True)
(EXTRACTED_MEDIA_DIR / "tables").mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
