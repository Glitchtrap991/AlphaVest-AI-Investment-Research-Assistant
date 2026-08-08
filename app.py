"""
app.py — Streamlit entry point for AlphaVest Research Assistant.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import streamlit as st

from src.config import UPLOADS_DIR
try:
    from src.tools.pdf_rag_tool import build_knowledge_base, get_knowledge_base_stats
except ImportError:
    from src.tools.pdf_rag_tool import build_knowledge_base

    def get_knowledge_base_stats() -> dict:
        return {"total_files": 0, "total_chunks": 0, "files_info": [], "raw_chunks": []}

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AlphaVest — AI Investment Research Assistant",
    page_icon="📈",
    layout="wide",
)

# ── Custom Styling (Larger Chat Input & Text) ────────────────────────────────
st.markdown(
    """
    <style>
    /* Chat input box text size & padding */
    div[data-testid="stChatInput"] textarea {
        font-size: 1.15rem !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        min-height: 60px !important;
        padding: 12px 16px !important;
    }

    /* Chat message text readability */
    div[data-testid="stChatMessage"] {
        font-size: 1.05rem !important;
        line-height: 1.65 !important;
    }

    /* Input container rounding & shadow */
    div[data-testid="stChatInput"] {
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state defaults ───────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_report_text" not in st.session_state:
    st.session_state.last_report_text = None
if "email_toast_shown" not in st.session_state:
    st.session_state.email_toast_shown = False


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
        st.rerun()

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


# ── Header & Main Navigation ──────────────────────────────────────────────────
st.title("📈 AlphaVest — AI Investment Research Assistant")
st.caption("Autonomous AI assistant for financial research, RAG report analysis, calculations, and email summaries.")

tab_chat, tab_calc, tab_dashboard = st.tabs([
    "💬 AI Research Assistant",
    "🧮 Financial Calculator",
    "📊 Knowledge Base Dashboard"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: AI RESEARCH ASSISTANT (CHAT)
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Expandable details
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

                if details.get("email_status"):
                    st.success(f"📧 {details['email_status']}")

                if details.get("recommendation"):
                    with st.expander("💡 Final Recommendation"):
                        st.markdown(details["recommendation"])

    # Download report button (if a report exists)
    if st.session_state.last_report_text:
        st.download_button(
            label="📥 Download Report (.txt)",
            data=st.session_state.last_report_text,
            file_name="investment_report.txt",
            mime="text/plain",
        )

    # Chat Input
    user_input = st.chat_input("Ask about any company, market, calculation, or uploaded report…")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Invoke agent
        with st.chat_message("assistant"):
            with st.spinner("Researching…"):
                from src.agent import run_agent
                result = run_agent(user_input, st.session_state.thread_id)

            messages = result.get("messages", [])
            assistant_text = ""
            details = {
                "sources": "",
                "pdf_chunks": "",
                "calculations": "",
                "recommendation": "",
                "email_status": "",
            }

            for msg in messages:
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
                        elif tool_name == "send_email":
                            details["email_status"] = content
                            st.toast("📧 Success: Email dispatched!", icon="✅")

                    elif msg.type == "ai" and getattr(msg, "content", ""):
                        assistant_text = msg.content

            # Check for investment report
            report_keywords = ["Company Overview", "Investment Summary", "Strengths", "Weaknesses"]
            if sum(1 for kw in report_keywords if kw.lower() in assistant_text.lower()) >= 3:
                st.session_state.last_report_text = assistant_text
                details["recommendation"] = _extract_recommendation(assistant_text)
            else:
                st.session_state.last_report_text = None

            st.markdown(assistant_text)

            if details["email_status"]:
                st.success(f"📧 {details['email_status']}")
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

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "details": details,
            })


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: FINANCIAL CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:
    st.subheader("🧮 Financial & Investment Calculator")
    st.caption("Perform instant metric calculations and generate structured financial comparison matrices.")

    calc_option = st.selectbox(
        "Select Calculation Type",
        ["CAGR (Compound Annual Growth Rate)", "Growth Percentage (%)", "Return on Investment (ROI)", "Company Comparison Table"]
    )

    st.divider()

    if calc_option == "CAGR (Compound Annual Growth Rate)":
        col1, col2, col3 = st.columns(3)
        with col1:
            beg_val = st.number_input("Beginning Value ($)", min_value=0.01, value=100.0, step=10.0)
        with col2:
            end_val = st.number_input("Ending Value ($)", min_value=0.01, value=250.0, step=10.0)
        with col3:
            years = st.number_input("Number of Years", min_value=0.1, value=5.0, step=0.5)

        if st.button("Compute CAGR"):
            cagr = (end_val / beg_val) ** (1 / years) - 1
            st.metric("CAGR (%)", f"{cagr:.2%}")
            st.info(f"**Formula**: `({end_val} / {beg_val}) ^ (1 / {years}) - 1` = **{cagr:.2%}**")

    elif calc_option == "Growth Percentage (%)":
        col1, col2 = st.columns(2)
        with col1:
            old_val = st.number_input("Old Value", value=100.0, step=10.0)
        with col2:
            new_val = st.number_input("New Value", value=175.0, step=10.0)

        if st.button("Compute Growth %"):
            if old_val != 0:
                pct = ((new_val - old_val) / abs(old_val)) * 100
                st.metric("Growth %", f"{pct:+.2f}%")
                st.info(f"**Formula**: `({new_val} - {old_val}) / {old_val} * 100` = **{pct:+.2f}%**")
            else:
                st.error("Old value cannot be zero.")

    elif calc_option == "Return on Investment (ROI)":
        col1, col2 = st.columns(2)
        with col1:
            gain = st.number_input("Net Investment Gain ($)", value=500.0, step=50.0)
        with col2:
            cost = st.number_input("Initial Investment Cost ($)", min_value=0.01, value=2000.0, step=100.0)

        if st.button("Compute ROI"):
            roi = (gain / cost) * 100
            st.metric("ROI (%)", f"{roi:.2f}%")
            st.info(f"**Formula**: `({gain} / {cost}) * 100` = **{roi:.2f}%**")

    elif calc_option == "Company Comparison Table":
        st.write("Generate a formatted markdown comparison table for two companies.")
        col1, col2 = st.columns(2)
        with col1:
            co1_name = st.text_input("Company 1 Name", "NVIDIA")
            co1_rev = st.text_input("Company 1 Revenue", "$96.3B")
            co1_pe = st.text_input("Company 1 P/E Ratio", "48.2")
        with col2:
            co2_name = st.text_input("Company 2 Name", "AMD")
            co2_rev = st.text_input("Company 2 Revenue", "$22.7B")
            co2_pe = st.text_input("Company 2 P/E Ratio", "35.1")

        if st.button("Build Comparison Table"):
            table_md = f"""
| Metric | {co1_name} | {co2_name} |
|---|---|---|
| Revenue | {co1_rev} | {co2_rev} |
| P/E Ratio | {co1_pe} | {co2_pe} |
            """
            st.markdown(table_md)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: KNOWLEDGE BASE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dashboard:
    st.subheader("📊 Uploaded Reports & Knowledge Base Breakdown")
    st.caption("Explore indexed vector database statistics, file metrics, and retrieved chunk details.")

    stats = get_knowledge_base_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Uploaded Files", stats["total_files"])
    with col2:
        st.metric("🧩 Indexed Chunks", stats["total_chunks"])
    with col3:
        status_label = "🟢 Ready" if stats["total_chunks"] > 0 else "🟡 Needs Build"
        st.metric("Vector Database", status_label)

    st.divider()

    # Detailed File Table
    st.write("### 📄 Uploaded Document Breakdown")
    if stats["files_info"]:
        st.dataframe(
            stats["files_info"],
            column_config={
                "filename": "File Name",
                "size_kb": "Size (KB)",
                "chunks": "Indexed Chunks",
                "path": "Full Path",
            },
            use_container_width=True,
        )
    else:
        st.info("No uploaded files found. Upload PDFs in the sidebar and click 'Build Knowledge Base'.")

    # Chunk Inspector
    if stats["raw_chunks"]:
        st.write("### 🔍 Raw Chunk Inspector")
        chunk_idx = st.slider("Select Chunk Index", 0, len(stats["raw_chunks"]) - 1, 0)
        selected_chunk = stats["raw_chunks"][chunk_idx]

        st.json(selected_chunk["meta"])
        st.text_area("Chunk Content", selected_chunk["doc"], height=200)


def _extract_recommendation(text: str) -> str:
    """Extract the Investment Summary section from a report text."""
    lower = text.lower()
    markers = ["investment summary", "recommendation", "overall assessment"]
    for marker in markers:
        idx = lower.find(marker)
        if idx != -1:
            return text[idx:]
    return ""
