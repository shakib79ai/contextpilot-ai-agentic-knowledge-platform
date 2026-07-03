import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReviewPriority, ReviewStatus


class ReviewTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    answer_id: uuid.UUID
    status: ReviewStatus
    priority: ReviewPriority
    reason: str | None
    created_at: datetime
    resolved_at: datetime | None = None


class ReviewResolveRequest(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    corrected_content: str | None = None
    note: str | None = None
