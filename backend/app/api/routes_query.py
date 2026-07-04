from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.conversation import Answer, Conversation, Message
from app.models.enums import AnswerStatus, MessageRole, ReviewPriority, ReviewStatus
from app.models.review import ReviewTask
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse
from agents.graph import run_query_graph

router = APIRouter(prefix="/query", tags=["query"])

WITHHELD_MESSAGE = (
    "This question requires human review before a confident answer can be provided. "
    "You'll be notified once a reviewer has verified a response."
)


@router.post("", response_model=QueryResponse)
def ask_question(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = None
    if payload.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
    if conversation is None:
        conversation = Conversation(user_id=current_user.id, title=payload.question[:80])
        db.add(conversation)
        db.flush()

    user_message = Message(conversation_id=conversation.id, role=MessageRole.user, content=payload.question)
    db.add(user_message)
    db.flush()

    result_state = run_query_graph(payload.question, top_k=5, db=db)

    status_value = result_state.get("status", AnswerStatus.escalated.value)
    is_escalated = status_value == AnswerStatus.escalated.value

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.assistant,
        content=result_state.get("answer_content", ""),
    )
    db.add(assistant_message)
    db.flush()

    answer = Answer(
        message_id=assistant_message.id,
        content=result_state.get("answer_content", ""),
        confidence_score=result_state.get("confidence", 0.0),
        status=AnswerStatus(status_value),
        citations_json=result_state.get("citations", []),
        score_breakdown_json=result_state.get("score_breakdown", {}),
    )
    db.add(answer)
    db.flush()

    if status_value in (AnswerStatus.escalated.value, AnswerStatus.low_confidence.value):
        db.add(
            ReviewTask(
                answer_id=answer.id,
                status=ReviewStatus.pending,
                priority=ReviewPriority.high if is_escalated else ReviewPriority.low,
                reason=result_state.get("review_reason"),
            )
        )

    db.commit()
    db.refresh(answer)

    breakdown = result_state.get(
        "score_breakdown",
        {"retrieval_quality": 0.0, "source_relevance": 0.0, "self_check_score": 0.0, "historical_feedback_score": 0.0, "confidence": 0.0},
    )

    return QueryResponse(
        answer_id=answer.id,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        content=WITHHELD_MESSAGE if is_escalated else answer.content,
        status=answer.status,
        confidence_score=answer.confidence_score,
        score_breakdown=breakdown,
        citations=[] if is_escalated else result_state.get("citations", []),
        pending_review=status_value in (AnswerStatus.escalated.value, AnswerStatus.low_confidence.value),
    )
