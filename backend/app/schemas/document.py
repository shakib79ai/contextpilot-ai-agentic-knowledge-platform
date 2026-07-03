import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str | None
    status: DocumentStatus
    error_reason: str | None = None
    uploaded_at: datetime
    indexed_at: datetime | None = None
