from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.conversation import Answer
from app.models.enums import AnswerStatus, FeedbackKind, UserRole
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from context_learning.feedback_store import record_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])

# reviewer_approve/reviewer_edit/reviewer_reject are meant to be produced only
# by the reviewer-gated /review/{id}/resolve flow — never by this end-user
# endpoint, since they feed directly into historical_feedback_score and
# admin-facing stats. Restricting `kind` here prevents any authenticated
# member from injecting fake reviewer signals.
REVIEWER_ONLY_KINDS = {FeedbackKind.reviewer_approve, FeedbackKind.reviewer_edit, FeedbackKind.reviewer_reject}


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.kind in REVIEWER_ONLY_KINDS and current_user.role not in (UserRole.reviewer, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers can submit reviewer feedback; use thumbs_up/thumbs_down.",
        )

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
