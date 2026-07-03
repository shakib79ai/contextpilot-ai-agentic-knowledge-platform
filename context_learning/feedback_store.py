"""Persists feedback events — the raw material the Learning Engine turns
into improved future context. See context-learning-engine.md."""
import uuid

from sqlalchemy.orm import Session

from app.models.enums import FeedbackKind
from app.models.feedback import FeedbackEvent


def record_feedback(
    db: Session,
    answer_id: uuid.UUID,
    user_id: uuid.UUID,
    kind: FeedbackKind,
    comment: str | None = None,
    corrected_content: str | None = None,
) -> FeedbackEvent:
    event = FeedbackEvent(
        answer_id=answer_id,
        user_id=user_id,
        kind=kind,
        comment=comment,
        corrected_content=corrected_content,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def feedback_summary(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {kind.value: 0 for kind in FeedbackKind}
    for event in db.query(FeedbackEvent).all():
        counts[event.kind.value] += 1
    return counts
