"""
src/tools/memory_tools.py — Long-term investor profile memory (SQLite).

Two tools:
  - remember_preference: persist a fact about the investor
  - recall_preferences: retrieve all stored facts
"""
from __future__ import annotations
from langgraph.checkpoint.sqlite import sqlite3
# import sqlite3
from contextlib import contextmanager

from langchain_core.tools import tool

from src.config import INVESTOR_MEMORY_DB

# ── Database setup ───────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS investor_profile (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

# Valid preference keys (matches spec §9)
_VALID_KEYS = {
    "client_name",
    "investment_interests",
    "preferred_industries",
    "risk_profile",
    "frequently_researched_companies",
}


@contextmanager
def _get_db():
    """Yield a SQLite connection with auto-commit."""
    conn = sqlite3.connect(str(INVESTOR_MEMORY_DB))
    conn.execute(_CREATE_TABLE)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── Tools ────────────────────────────────────────────────────────────────────

@tool
def remember_preference(key: str, value: str) -> str:
    """Save a fact about the investor to long-term memory.

    Use this when the user tells you their name, risk tolerance, preferred
    industries, investment interests, or frequently researched companies.

    Args:
        key: One of: client_name, investment_interests, preferred_industries,
             risk_profile, frequently_researched_companies.
        value: The value to store (e.g. "low-risk technology investments").

    Returns:
        Confirmation that the preference was saved.
    """
    normalised_key = key.strip().lower().replace(" ", "_")

    if normalised_key not in _VALID_KEYS:
        return (
            f"Unknown preference key '{key}'. "
            f"Valid keys: {', '.join(sorted(_VALID_KEYS))}."
        )

    with _get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO investor_profile (key, value) VALUES (?, ?)",
            (normalised_key, value.strip()),
        )

    return f"✅ Remembered: {normalised_key} = '{value.strip()}'."


@tool
def recall_preferences() -> str:
    """Retrieve all stored investor preferences from long-term memory.

    Use this when you need to personalise a response based on the investor's
    profile, risk tolerance, or interests.

    Returns:
        All stored investor preferences, or a message if none are stored.
    """
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT key, value FROM investor_profile ORDER BY key"
        ).fetchall()

    if not rows:
        return "No investor preferences stored yet."

    lines = [f"  • {k}: {v}" for k, v in rows]
    return "Investor Profile:\n" + "\n".join(lines)
