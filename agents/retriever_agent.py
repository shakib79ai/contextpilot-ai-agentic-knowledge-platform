"""Retriever Agent: finds the most relevant knowledge for the question."""
from app.config import get_settings
from agents.state import AgentState
from rag_pipeline.retriever import Retriever

_retriever: Retriever | None = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever(get_settings())
    return _retriever


def run(state: AgentState) -> AgentState:
    top_k = state.get("top_k", 5)
    chunks = _get_retriever().retrieve(state["question"], top_k=top_k)
    state["retrieved_chunks"] = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "content": c.content,
            "similarity": c.similarity,
            "source": c.source,
        }
        for c in chunks
    ]
    return state
