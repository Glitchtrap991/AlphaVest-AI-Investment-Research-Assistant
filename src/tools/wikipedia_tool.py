"""
src/tools/wikipedia_tool.py — Wikipedia lookup tool.
"""
from __future__ import annotations

from langchain_core.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


_wiki_api = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=4000)
_wiki = WikipediaQueryRun(api_wrapper=_wiki_api)


@tool
def wikipedia_lookup(query: str) -> str:
    """Look up background facts about a company or topic on Wikipedia.

    Use this for established facts: company history, founding date, CEO,
    headquarters, product lines, industry classification, etc.

    Args:
        query: The topic to look up (e.g. "NVIDIA Corporation").

    Returns:
        A summary from Wikipedia.
    """
    try:
        return _wiki.invoke(query)
    except Exception as e:
        return f"Could not retrieve Wikipedia facts for '{query}' (API error/rate limit: {e}). Use web_search instead."
