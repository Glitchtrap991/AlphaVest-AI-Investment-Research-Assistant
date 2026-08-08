"""
src/tools/search_tool.py — DuckDuckGo web search tool.
"""
from __future__ import annotations

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool


_ddg = DuckDuckGoSearchResults(num_results=5)


@tool
def web_search(query: str) -> str:
    """Search the web for current news and information using DuckDuckGo.

    Use this tool to find recent news, stock updates, company announcements,
    market trends, or any real-time information about companies and investments.

    Args:
        query: The search query string (e.g. "NVIDIA latest AI announcements 2025").

    Returns:
        Search results with titles, snippets, and URLs.
    """
    try:
        return _ddg.invoke(query)
    except Exception as e:
        return f"Web search error for '{query}': {e}. Proceed with available tools or information."
