import uuid

from pydantic import BaseModel

from app.models.enums import AnswerStatus


class QueryRequest(BaseModel):
    question: str
    conversation_id: uuid.UUID | None = None


class Citation(BaseModel):
    chunk_id: str
    document_id: str | None = None
    snippet: str
    similarity: float
    source: str = "document"


class ScoreBreakdown(BaseModel):
    retrieval_quality: float
    source_relevance: float
    self_check_score: float
    historical_feedback_score: float
    confidence: float


class QueryResponse(BaseModel):
    answer_id: uuid.UUID
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    status: AnswerStatus
    confidence_score: float
    score_breakdown: ScoreBreakdown
    citations: list[Citation]
    pending_review: bool
