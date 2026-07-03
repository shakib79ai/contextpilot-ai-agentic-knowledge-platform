import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_reviewer
from app.database import get_db
from app.models.conversation import Answer
from app.models.enums import AnswerStatus, FeedbackKind, ReviewStatus
from app.models.review import ReviewTask
from app.models.user import User
from app.schemas.review import ReviewResolveRequest, ReviewTaskRead
from context_learning.feedback_store import record_feedback
from context_learning.learning_engine import index_correction_now, propose_knowledge_update

router = APIRouter(prefix="/review", tags=["review"])


@router.get("", response_model=list[ReviewTaskRead])
def list_review_tasks(
    review_status: ReviewStatus | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_reviewer),
):
    query = db.query(ReviewTask)
    if review_status is not None:
        query = query.filter(ReviewTask.status == review_status)
    return query.order_by(ReviewTask.priority.desc(), ReviewTask.created_at.asc()).all()


@router.post("/{task_id}/claim", response_model=ReviewTaskRead)
def claim_review_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer),
):
    task = db.get(ReviewTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review task not found")

    task.status = ReviewStatus.in_review
    task.assigned_to = reviewer.id
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/resolve", response_model=ReviewTaskRead)
def resolve_review_task(
    task_id: uuid.UUID,
    payload: ReviewResolveRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer),
):
    task = db.get(ReviewTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review task not found")

    answer = db.get(Answer, task.answer_id)
    if answer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    if payload.decision == "approve":
        answer.status = AnswerStatus.reviewed_approved
        record_feedback(db, answer.id, reviewer.id, FeedbackKind.reviewer_approve, comment=payload.note)

    elif payload.decision == "reject":
        answer.status = AnswerStatus.reviewed_rejected
        record_feedback(db, answer.id, reviewer.id, FeedbackKind.reviewer_reject, comment=payload.note)

    elif payload.decision == "edit":
        if not payload.corrected_content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="corrected_content is required for an edit decision")

        answer.content = payload.corrected_content
        answer.status = AnswerStatus.reviewed_edited
        record_feedback(
            db,
            answer.id,
            reviewer.id,
            FeedbackKind.reviewer_edit,
            comment=payload.note,
            corrected_content=payload.corrected_content,
        )

        # Immediately index the correction as high-trust retrievable context,
        # and (if it looks like a factual change) propose a formal knowledge update.
        index_correction_now(db, answer, payload.corrected_content)
        propose_knowledge_update(db, answer, payload.corrected_content)

    task.status = ReviewStatus.resolved
    task.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task
