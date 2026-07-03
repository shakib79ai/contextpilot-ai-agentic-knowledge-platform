from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.conversation import Answer
from app.models.enums import AnswerStatus, FeedbackKind
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from context_learning.feedback_store import record_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    answer = db.get(Answer, payload.answer_id)
    if answer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    event = record_feedback(
        db,
        answer_id=answer.id,
        user_id=current_user.id,
        kind=payload.kind,
        comment=payload.comment,
        corrected_content=payload.corrected_content,
    )

    if payload.kind == FeedbackKind.thumbs_down and answer.status == AnswerStatus.auto_answered:
        from app.models.enums import ReviewPriority, ReviewStatus
        from app.models.review import ReviewTask

        existing = db.query(ReviewTask).filter(ReviewTask.answer_id == answer.id).first()
        if existing is None:
            db.add(
                ReviewTask(
                    answer_id=answer.id,
                    status=ReviewStatus.pending,
                    priority=ReviewPriority.normal,
                    reason="User submitted thumbs-down feedback on a previously auto-answered response.",
                )
            )
            db.commit()

    return FeedbackRead(id=event.id, answer_id=event.answer_id, kind=event.kind, comment=event.comment)
