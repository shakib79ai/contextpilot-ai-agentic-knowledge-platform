"""Turns reviewer feedback into retrievable context. See
context-learning-engine.md for the full design rationale.

Two distinct mechanisms:
  1. `index_correction_now` — immediately re-embeds a reviewer's corrected
     answer as a first-class, high-trust `human_correction` chunk so future
     similar questions retrieve the fix, not the stale original.
  2. `propose_knowledge_update` — if the correction looks like a factual
     change to a *source document* (not just phrasing), proposes a formal
     `KnowledgeUpdate` for a second reviewer to approve/apply back onto the
     document itself.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from agents.knowledge_update_agent import propose_update
from app.config import get_settings
from app.models.conversation import Answer
from app.models.document import Chunk
from app.models.review import KnowledgeUpdate
from rag_pipeline.retriever import Retriever

STALENESS_DAYS = 90


def index_correction_now(db: Session, answer: Answer, corrected_content: str) -> Chunk:
    correction_chunk = Chunk(
        document_id=None,
        content=corrected_content,
        token_count=max(1, len(corrected_content) // 4),
        chunk_index=0,
        source="human_correction",
        metadata_json={"corrected_answer_id": str(answer.id), "verified_at": datetime.now(timezone.utc).isoformat()},
    )
    db.add(correction_chunk)
    db.flush()

    retriever = Retriever(get_settings())
    retriever.index_correction(
        chunk_id=str(correction_chunk.id),
        content=corrected_content,
        metadata={
            "document_id": None,
            "chunk_index": 0,
            "filename": "human_correction",
        },
    )
    correction_chunk.embedding_id = str(correction_chunk.id)
    db.commit()
    db.refresh(correction_chunk)
    return correction_chunk


def propose_knowledge_update(db: Session, answer: Answer, corrected_content: str) -> KnowledgeUpdate | None:
    """Looks at the top document-sourced citation on `answer` and, if the
    correction represents a factual drift from it, creates a proposed
    KnowledgeUpdate for a second reviewer to approve."""
    document_citations = [c for c in (answer.citations_json or []) if c.get("source") == "document"]
    if not document_citations:
        return None

    top_citation = document_citations[0]
    chunk_id = top_citation.get("chunk_id")
    original_chunk = db.get(Chunk, uuid.UUID(chunk_id)) if chunk_id else None
    if original_chunk is None:
        return None

    proposal = propose_update(original_chunk.content, corrected_content)
    if proposal is None:
        return None

    update = KnowledgeUpdate(
        source_document_id=original_chunk.document_id,
        chunk_id=original_chunk.id,
        proposed_content=proposal["proposed_content"],
        reason=proposal["reason"],
    )
    db.add(update)
    db.commit()
    db.refresh(update)
    return update


def apply_knowledge_update(db: Session, update: KnowledgeUpdate) -> None:
    """Called once a second reviewer approves a KnowledgeUpdate: re-embeds
    the corrected content over the original chunk's slot in the vector
    store and marks the update applied."""
    from app.models.enums import KnowledgeUpdateStatus

    chunk = db.get(Chunk, update.chunk_id) if update.chunk_id else None
    if chunk is not None:
        chunk.content = update.proposed_content
        retriever = Retriever(get_settings())
        retriever.index_correction(
            chunk_id=str(chunk.id),
            content=update.proposed_content,
            metadata={
                "document_id": str(chunk.document_id) if chunk.document_id else None,
                "chunk_index": chunk.chunk_index,
                "filename": (chunk.metadata_json or {}).get("filename", ""),
            },
        )

    update.status = KnowledgeUpdateStatus.applied
    update.resolved_at = datetime.now(timezone.utc)
    db.commit()


def find_stale_corrections(db: Session, staleness_days: int = STALENESS_DAYS) -> list[Chunk]:
    """Corrections older than the staleness window that should be
    re-surfaced to a reviewer for re-confirmation."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=staleness_days)
    return (
        db.query(Chunk)
        .filter(Chunk.source == "human_correction", Chunk.created_at < cutoff)
        .all()
    )
