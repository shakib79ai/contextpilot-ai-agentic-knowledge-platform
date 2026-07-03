import uuid

from pydantic import BaseModel

from app.models.enums import FeedbackKind


class FeedbackCreate(BaseModel):
    answer_id: uuid.UUID
    kind: FeedbackKind
    comment: str | None = None
    corrected_content: str | None = None


class FeedbackRead(BaseModel):
    id: uuid.UUID
    answer_id: uuid.UUID
    kind: FeedbackKind
    comment: str | None
