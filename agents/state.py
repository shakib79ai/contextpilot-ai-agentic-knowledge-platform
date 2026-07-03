from typing import TypedDict


class RetrievedChunkDict(TypedDict):
    chunk_id: str
    document_id: str | None
    content: str
    similarity: float
    source: str


class ScoreBreakdownDict(TypedDict):
    retrieval_quality: float
    source_relevance: float
    self_check_score: float
    historical_feedback_score: float
    confidence: float


class AgentState(TypedDict, total=False):
    """Shared state threaded through the LangGraph agent graph."""

    question: str
    top_k: int

    retrieved_chunks: list[RetrievedChunkDict]

    answer_content: str
    citations: list[dict]

    score_breakdown: ScoreBreakdownDict
    confidence: float

    status: str  # AnswerStatus value, set by the Evaluator/Escalation agents
    review_reason: str | None
