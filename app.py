"""
app.py — Streamlit entry point for AlphaVest Research Assistant.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import streamlit as st

from src.config import UPLOADS_DIR
from src.tools.pdf_rag_tool import build_knowledge_base

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AlphaVest — AI Investment Research Assistant",
    page_icon="📈",
    layout="wide",
)

# ── Session state defaults ───────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_report_text" not in st.session_state:
    st.session_state.last_report_text = None


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Document Management")

    # Upload PDFs
    uploaded_files = st.file_uploader(
        "Upload Annual / Quarterly Reports",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for uf in uploaded_files:
            dest = UPLOADS_DIR / uf.name
            if not dest.exists():
                dest.write_bytes(uf.getvalue())
                st.success(f"Uploaded: {uf.name}")

    # Build Knowledge Base
    if st.button("🔨 Build Knowledge Base", use_container_width=True):
        with st.spinner("Processing PDFs & building embeddings…"):
            status = build_knowledge_base()
        st.info(status)

    # View Uploaded Reports
    st.subheader("📄 Uploaded Reports")
    pdf_files = sorted(UPLOADS_DIR.glob("*.pdf"))
    if pdf_files:
        for pf in pdf_files:
            st.text(f"• {pf.name}")
    else:
        st.caption("No reports uploaded yet.")

    st.divider()

    # Clear Chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.last_report_text = None
        st.rerun()


# ── Main Chat Area ───────────────────────────────────────────────────────────
st.title("📈 AlphaVest — AI Investment Research Assistant")
st.caption("Ask me to research companies, compare investments, analyze reports, or email summaries.")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Expandable details (collapsed by default)
        if msg["role"] == "assistant" and msg.get("details"):
            details = msg["details"]

            if details.get("sources"):
                with st.expander("🔗 Sources Used"):
                    st.markdown(details["sources"])

            if details.get("pdf_chunks"):
                with st.expander("📄 Retrieved PDF Chunks"):
                    st.markdown(details["pdf_chunks"])

            if details.get("calculations"):
                with st.expander("🧮 Calculations Performed"):
                    st.markdown(details["calculations"])

            if details.get("recommendation"):
                with st.expander("💡 Final Recommendation"):
                    st.markdown(details["recommendation"])

# Download report button (outside chat, only if a report exists)
if st.session_state.last_report_text:
    st.download_button(
        label="📥 Download Report (.txt)",
        data=st.session_state.last_report_text,
        file_name="investment_report.txt",
        mime="text/plain",
    )

# ── Chat Input ───────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about any company, market, or investment…")

if user_input:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Invoke agent
    with st.chat_message("assistant"):
        with st.spinner("Researching…"):
            # Import here to avoid loading the agent at module level on every rerun
            from src.agent import run_agent

            result = run_agent(user_input, st.session_state.thread_id)

        # Extract the final assistant message
        messages = result.get("messages", [])
        assistant_text = ""
        details = {
            "sources": "",
            "pdf_chunks": "",
            "calculations": "",
            "recommendation": "",
        }

        for msg in messages:
            # Tool messages carry intermediate results
            if hasattr(msg, "type"):
                if msg.type == "tool":
                    tool_name = getattr(msg, "name", "")
                    content = getattr(msg, "content", "")

                    if tool_name in ("web_search", "wikipedia_lookup"):
                        details["sources"] += f"**{tool_name}:**\n{content}\n\n"
                    elif tool_name == "search_uploaded_reports":
                        details["pdf_chunks"] += content + "\n\n"
                    elif tool_name == "run_financial_calculation":
                        details["calculations"] += content + "\n\n"

                elif msg.type == "ai" and getattr(msg, "content", ""):
                    assistant_text = msg.content

        # Check if this looks like an investment report (contains key sections)
        report_keywords = ["Company Overview", "Investment Summary", "Strengths", "Weaknesses"]
        if sum(1 for kw in report_keywords if kw.lower() in assistant_text.lower()) >= 3:
            st.session_state.last_report_text = assistant_text
            details["recommendation"] = _extract_recommendation(assistant_text)
        else:
            st.session_state.last_report_text = None

        st.markdown(assistant_text)

        # Show expandable details
        if details["sources"]:
            with st.expander("🔗 Sources Used"):
                st.markdown(details["sources"])
        if details["pdf_chunks"]:
            with st.expander("📄 Retrieved PDF Chunks"):
                st.markdown(details["pdf_chunks"])
        if details["calculations"]:
            with st.expander("🧮 Calculations Performed"):
                st.markdown(details["calculations"])
        if details["recommendation"]:
            with st.expander("💡 Final Recommendation"):
                st.markdown(details["recommendation"])

        # Save to session
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "details": details,
        })


def _extract_recommendation(text: str) -> str:
    """Extract the Investment Summary section from a report text."""
    lower = text.lower()
    markers = ["investment summary", "recommendation", "overall assessment"]
    for marker in markers:
        idx = lower.find(marker)
        if idx != -1:
            # Return from the marker to the end
            return text[idx:]
    return ""
