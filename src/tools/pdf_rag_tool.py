"""
src/tools/pdf_rag_tool.py — ChromaDB-backed PDF retrieval tool.

Provides:
  - build_knowledge_base()  — called by the Streamlit sidebar button
  - get_search_uploaded_reports_tool() — returns the agent-bindable tool
"""
from __future__ import annotations

import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHROMA_DIR, UPLOADS_DIR


# ── Shared Chroma client (persistent) ───────────────────────────────────────
_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_COLLECTION_NAME = "uploaded_reports"


def build_knowledge_base() -> str:
    """Read all PDFs in data/uploads/, chunk, embed into ChromaDB.

    Called by the Streamlit 'Build Knowledge Base' button, NOT by the agent.
    Returns a status message.
    """
    pdf_files = list(UPLOADS_DIR.glob("*.pdf"))
    if not pdf_files:
        return "No PDF files found in data/uploads/."

    # Delete existing collection to rebuild fresh
    try:
        _chroma_client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass

    collection = _chroma_client.get_or_create_collection(
        name=_COLLECTION_NAME,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    total_chunks = 0
    for pdf_path in pdf_files:
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        chunks = splitter.split_documents(pages)

        for i, chunk in enumerate(chunks):
            doc_id = f"{pdf_path.stem}_{i}"
            collection.add(
                ids=[doc_id],
                documents=[chunk.page_content],
                metadatas=[{
                    "source": pdf_path.name,
                    "page": chunk.metadata.get("page", 0),
                }],
            )
        total_chunks += len(chunks)

    return f"✅ Processed {len(pdf_files)} PDF(s), {total_chunks} chunks indexed."


@tool
def search_uploaded_reports(query: str) -> str:
    """Search the uploaded knowledge base / PDF documents for relevant information.

    ALWAYS check this tool when answering questions, researching topics, analyzing companies,
    or looking up details that could be in uploaded PDF documents or reports.

    Args:
        query: The question or topic to search for in the uploaded documents.

    Returns:
        Relevant excerpts from the uploaded documents.
    """
    try:
        collection = _chroma_client.get_collection(name=_COLLECTION_NAME)
    except Exception:
        return "No knowledge base found. Please upload reports and click 'Build Knowledge Base' first."

    if collection.count() == 0:
        return "Knowledge base is empty. Please upload reports and click 'Build Knowledge Base' first."

    results = collection.query(
        query_texts=[query],
        n_results=5,
    )

    if not results["documents"] or not results["documents"][0]:
        return "No relevant information found in uploaded reports."

    output_parts: list[str] = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source = meta.get("source", "unknown")
        page = meta.get("page", "?")
        output_parts.append(f"[{source}, p.{page}]\n{doc}")

    return "\n\n---\n\n".join(output_parts)
