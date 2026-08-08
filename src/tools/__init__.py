"""
src/tools/__init__.py — Tools package exports.
"""
from __future__ import annotations

from src.tools.pdf_rag_tool import build_knowledge_base, get_knowledge_base_stats, search_uploaded_reports
from src.tools.search_tool import web_search
from src.tools.wikipedia_tool import wikipedia_lookup
from src.tools.finance_calc_tool import run_financial_calculation
from src.tools.gmail_tool import send_email
from src.tools.memory_tools import remember_preference, recall_preferences

__all__ = [
    "build_knowledge_base",
    "get_knowledge_base_stats",
    "search_uploaded_reports",
    "web_search",
    "wikipedia_lookup",
    "run_financial_calculation",
    "send_email",
    "remember_preference",
    "recall_preferences",
]
