"""
Global configuration loader for DeepThink.
Loads environment variables from .env and settings from configuration-example/config.example.json.
"""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Graceful dotenv loader
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# API Keys
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Model Names
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "voyage-4")

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
CORPUS_DIR = PROJECT_ROOT / os.getenv("ASSET_CORPUS_DIR", "data/ashen_era_archive")
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
