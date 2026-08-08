# AlphaVest — AI Investment & Financial Research Assistant

A Streamlit app powered by a **single LangGraph agent** that helps investors research companies, analyze reports, compare investments, and email summaries — all through natural-language conversation.

## Architecture

```
Investor
   ↓
Streamlit UI  (chat box + sidebar)
   ↓
Single LangGraph Agent  ── bound to 7 tools ──┐
   │                                            │
   ├── web_search (DuckDuckGo)                  │
   ├── wikipedia_lookup                         │
   ├── search_uploaded_reports (ChromaDB RAG)   │
   ├── run_financial_calculation                │
   ├── send_email (Gmail)                       │
   ├── remember_preference (SQLite)             │
   └── recall_preferences (SQLite)              │
   ↓
LangGraph Checkpointer (short-term memory, per thread_id)
```

**One agent, one tool-calling loop.** No orchestration layer, no router, no multi-agent system.

## Setup

### 1. Clone & install

```bash
git clone <repo-url>
cd alphavest-research-assistant

# With uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required:
- `GROQ_API_KEY` — Get one free at [console.groq.com](https://console.groq.com)
- `GROQ_MODEL_NAME` — Default: `meta-llama/llama-4-maverick-17b-128e-instruct`

Optional (for email):
- `CLIENT_ID` / `CLIENT_SECRET` — Google Cloud Console OAuth credentials
- Place `credentials.json` in the project root for Gmail API access

### 3. Gmail setup (optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` to the project root
5. On first email send, complete the OAuth flow in your browser

If Gmail is not configured, the `send_email` tool will show an email preview instead of actually sending.

### 4. Run

```bash
streamlit run app.py
```

## Usage

### Sidebar
- **Upload Reports** — Drag PDF annual/quarterly reports
- **Build Knowledge Base** — Index uploaded PDFs into ChromaDB
- **View Uploaded Reports** — List of indexed documents
- **Clear Chat** — Start a fresh conversation (long-term memory is preserved)

### Chat
Ask natural-language questions like:
- "Research NVIDIA and summarize the latest AI announcements"
- "Compare Microsoft, Google, Amazon, and Meta"
- "Remember that I prefer low-risk technology investments"
- "Generate today's investment report and email it to my client"

### Expandable Details
Each response includes collapsible sections for:
- 🔗 Sources Used (news/wiki results)
- 📄 Retrieved PDF Chunks
- 🧮 Calculations Performed
- 💡 Final Recommendation

## Project Structure

```
alphavest-research-assistant/
├── app.py                        # Streamlit entry point
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   ├── uploads/                  # user-uploaded PDFs
│   └── chroma_db/                # persisted Chroma vector store
├── memory/
│   ├── checkpoints.db            # LangGraph SqliteSaver
│   └── investor_memory.db        # long-term investor profile
└── src/
    ├── config.py                 # env vars, model settings
    ├── schemas.py                # Pydantic InvestmentReport model
    ├── agent.py                  # the single LangGraph agent
    └── tools/
        ├── search_tool.py        # DuckDuckGo
        ├── wikipedia_tool.py
        ├── pdf_rag_tool.py       # ChromaDB retriever
        ├── finance_calc_tool.py  # CAGR / growth / ROI
        ├── gmail_tool.py
        └── memory_tools.py       # remember / recall preferences
```

## Test Scenarios

1. **"Research NVIDIA and summarize the latest AI announcements."**
2. **"Analyze Google's annual report and compare it with the latest news."**
3. **"Compare Microsoft, Google, Amazon, and Meta."**
4. **"Remember that I prefer low-risk technology investments."**
5. **"Generate today's investment report and email it to my client."**

## Memory Design

| Type | Mechanism | Persistence |
|------|-----------|-------------|
| Short-term (thread) | LangGraph checkpointer (`SqliteSaver`) | `memory/checkpoints.db` |
| Long-term (profile) | SQLite via `remember/recall_preferences` tools | `memory/investor_memory.db` |
| Document (RAG) | ChromaDB via `search_uploaded_reports` | `data/chroma_db/` |
