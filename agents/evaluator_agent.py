"""Evaluator Agent: scores accuracy, hallucination risk, and confidence."""
from app.config import get_settings
from agents.llm_client import get_chat_client
from agents.state import AgentState
from evals.confidence_scoring import score_answer


def run(state: AgentState, db=None) -> AgentState:
    settings = get_settings()
    chat_client = get_chat_client(settings)

    breakdown = score_answer(
        question=state["question"],
        answer_content=state.get("answer_content", ""),
        chunks=state.get("retrieved_chunks", []),
        chat_client=chat_client,
        db=db,
    )

    state["score_breakdown"] = breakdown
    state["confidence"] = breakdown["confidence"]
    return state
