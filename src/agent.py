"""
src/agent.py — Single LangGraph agent with all tools.

This is the ONLY agent in the project. No router, no coordinator,
no multi-agent orchestration. One agent, one tool-calling loop.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent

from src.config import CHECKPOINTS_DB, get_llm
from src.tools.finance_calc_tool import run_financial_calculation
from src.tools.gmail_tool import send_email
from src.tools.memory_tools import recall_preferences, remember_preference
from src.tools.pdf_rag_tool import search_uploaded_reports
from src.tools.search_tool import web_search
from src.tools.wikipedia_tool import wikipedia_lookup

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are AlphaVest, an expert AI investment research assistant.

Your job is to help investors research companies, analyze reports, compare
investments, and produce actionable insights. You have access to the following
tools — use them proactively:

TOOLS:
• search_uploaded_reports — Search uploaded PDF documents and knowledge base.
  ALWAYS check this tool first or alongside other tools for any topic or question,
  to ensure relevant information from uploaded files is included.
• web_search — Find current news, stock updates, company announcements, and
  market trends via DuckDuckGo. Always cite your sources.
• wikipedia_lookup — Get established background facts about companies
  (history, CEO, products, industry).
• run_financial_calculation — Compute CAGR, growth %, ROI, or build
  comparison tables. Pass a JSON string with the calculation type and values.
• send_email — Email a report or summary to a recipient via Gmail.
• remember_preference — Save investor preferences (name, risk profile,
  preferred industries, interests, frequently researched companies).
• recall_preferences — Retrieve stored investor profile information.

BEHAVIOR:
1. When answering any question or researching a topic, ALWAYS check `search_uploaded_reports`
   (knowledge base) to see if relevant uploaded documents or PDFs have information.
2. Use `web_search` and `wikipedia_lookup` to supplement with external facts when needed.
3. When asked to "compare" companies, research each one (sequential calls are
   fine), then write up a comparison with a markdown table.
4. When asked to "generate a report", gather information first (checking uploaded reports,
   web search, and wikipedia), then produce a well-structured investment report with these sections:
   - Company Overview, Industry, Business Model
   - Latest News, Strengths, Weaknesses
   - Financial Highlights, Growth Opportunities, Potential Risks
   - Investment Summary
5. When the user shares a personal preference (risk tolerance, interests),
   call remember_preference to persist it.
6. Before generating personalised recommendations, call recall_preferences to
   check for stored investor profile data.
7. AUTONOMOUS EMAIL DISPATCH (NEVER ASK FOR DETAILS):
   - When the user asks to send an email to an address or person about a topic (e.g. "alanbabuk12@gmail.com about azure clouds" or "email summary to client@alphavest.com"):
     a. NEVER ask the user to provide subject line, body text, or details! Be fully autonomous.
     b. Instantly research the topic first using `search_uploaded_reports`, `web_search`, or `wikipedia_lookup`.
     c. Create a professional subject line (e.g. "Research Overview & Key Insights: Azure Cloud Services").
     d. Compose a complete, high-quality, professional email body containing all findings, summaries, and key points.
     e. Immediately invoke `send_email(to=..., subject=..., body=...)` to send the email right away!

FORMAT:
- Use markdown for tables, bullet points, and section headers.
- Be concise but thorough. Cite sources where applicable.
- If information is unavailable, say so clearly instead of guessing.
"""

# ── Tool registry (complete list — 7 tools) ──────────────────────────────────

ALL_TOOLS = [
    search_uploaded_reports,
    web_search,
    wikipedia_lookup,
    run_financial_calculation,
    send_email,
    remember_preference,
    recall_preferences,
]

# ── Agent construction ───────────────────────────────────────────────────────

_conn = sqlite3.connect(str(CHECKPOINTS_DB), check_same_thread=False)
_checkpointer = SqliteSaver(_conn)

_agent = create_react_agent(
    model=get_llm(),
    tools=ALL_TOOLS,
    checkpointer=_checkpointer,
    prompt=SYSTEM_PROMPT,
)


def run_agent(user_message: str, thread_id: str) -> dict[str, Any]:
    """Invoke the agent and return the full result dict.

    Args:
        user_message: The user's natural-language query.
        thread_id: Unique identifier for this conversation thread.

    Returns:
        The agent's response dict including 'messages' list.
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = _agent.invoke(
        {"messages": [("human", user_message)]},
        config=config,
    )
    return result
