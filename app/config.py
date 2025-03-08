# File: gurbani-insight/app/config.py

"""
Configuration settings for the Gurbani Insight application.
Loads environment variables and provides default values.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Database settings
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "gurbani_english_enhanced")

# Embedding model settings
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/embeddings")

# Application settings
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8001"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Data paths
CSV_PATH = os.environ.get("CSV_PATH", "./data/gurbani_english_enhanced_chunks.csv")
PDF_PATH = os.environ.get("PDF_PATH", "./data/guru_granth_sahib.pdf")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create directories if they don't exist
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)