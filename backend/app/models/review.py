import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import KnowledgeUpdateStatus, ReviewPriority, ReviewStatus


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answers.id"), nullable=False, unique=True)
    assigned_to: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.pending, nullable=False)
    priority: Mapped[ReviewPriority] = mapped_column(Enum(ReviewPriority), default=ReviewPriority.normal)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime] = mapped_column(nullable=True)


class KnowledgeUpdate(Base):
    __tablename__ = "knowledge_updates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id"), nullable=True)
    proposed_content: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[KnowledgeUpdateStatus] = mapped_column(
        Enum(KnowledgeUpdateStatus), default=KnowledgeUpdateStatus.proposed, nullable=False
    )
    created_by_agent: Mapped[str] = mapped_column(default="knowledge_update_agent")
    reviewed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime] = mapped_column(nullable=True)
