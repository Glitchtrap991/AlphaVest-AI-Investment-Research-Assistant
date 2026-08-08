"""
src/config.py — centralised configuration & LLM factory.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ─────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")

# ── API Keys ─────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME: str = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")

# ── Gmail OAuth (optional) ───────────────────────────────────────────────────
GMAIL_CLIENT_ID: str = os.getenv("CLIENT_ID")
GMAIL_CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = _ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
MEMORY_DIR = _ROOT / "memory"

CHECKPOINTS_DB = MEMORY_DIR / "checkpoints.db"
INVESTOR_MEMORY_DB = MEMORY_DIR / "investor_memory.db"

# Ensure directories exist at import time
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ── LLM Factory ─────────────────────────────────────────────────────────────
def get_llm():
    """Return a LangChain-compatible chat model."""
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=GROQ_MODEL_NAME,
        api_key=GROQ_API_KEY,
        temperature=0.3,
    )
