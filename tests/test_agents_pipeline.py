"""End-to-end smoke test of the query-time agent pipeline running fully
offline (LLM_PROVIDER=local, dummy API keys) against an isolated FAISS
index, verifying the Retriever -> Answer -> Evaluator -> Escalation chain
produces a well-formed result without any network calls."""
import agents.answer_agent as answer_agent
import agents.escalation_agent as escalation_agent
import agents.evaluator_agent as evaluator_agent
import agents.retriever_agent as retriever_agent
from agents.state import AgentState


def test_query_pipeline_runs_fully_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("VECTOR_STORE_DIR", str(tmp_path / "vector_store"))
    monkeypatch.setenv("LLM_PROVIDER", "local")

    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    from rag_pipeline.embeddings import get_embedding_client
    from rag_pipeline.vector_store import get_vector_store

    embedding_client = get_embedding_client(settings)
    vector_store = get_vector_store(settings, dimension=embedding_client.dimension)
    content = "ContextPilot AI escalates low-confidence answers to a human reviewer instead of guessing."
    vector_store.upsert(
        ids=["chunk-1"],
        vectors=embedding_client.embed_documents([content]),
        metadatas=[{"document_id": None, "chunk_index": 0, "content": content, "filename": "test.txt", "source": "document"}],
    )

    retriever_agent._retriever = None  # reset module-level singleton to pick up the patched settings

    state: AgentState = {"question": "How does ContextPilot AI handle low-confidence answers?", "top_k": 3}
    state = retriever_agent.run(state)
    assert len(state["retrieved_chunks"]) == 1

    state = answer_agent.run(state)
    assert state["answer_content"]
    assert len(state["citations"]) == 1

    state = evaluator_agent.run(state, db=None)
    assert 0.0 <= state["confidence"] <= 1.0
    assert set(state["score_breakdown"].keys()) == {
        "retrieval_quality", "source_relevance", "self_check_score", "historical_feedback_score", "confidence",
    }

    state = escalation_agent.run(state)
    assert state["status"] in {"auto_answered", "low_confidence", "escalated"}

    get_settings.cache_clear()
