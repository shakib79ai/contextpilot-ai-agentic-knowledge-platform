"""Document ingestion: extract text -> chunk -> embed -> upsert into the
vector store -> persist Chunk rows in Postgres. Designed to be called either
directly (tests/scripts) or from a Celery task (`backend/app/tasks/indexing.py`).
"""
import logging
import os
from datetime import datetime, timezone
from uuid import UUID

from app.config import get_settings
from app.database import SessionLocal
from app.models.document import Chunk, Document
from app.models.enums import DocumentStatus
from rag_pipeline.chunker import chunk_text
from rag_pipeline.embeddings import get_embedding_client
from rag_pipeline.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def _extract_text(storage_path: str, content_type: str | None) -> str:
    if content_type == "application/pdf" or storage_path.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(storage_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    with open(storage_path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def ingest_document(document_id: UUID) -> None:
    """Runs the full ingestion pipeline for a single document. Safe to retry."""
    settings = get_settings()
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            logger.warning("ingest_document: document %s not found", document_id)
            return

        document.status = DocumentStatus.indexing
        db.commit()

        text = _extract_text(document.storage_path, document.content_type)
        chunks = chunk_text(text)
        if not chunks:
            document.status = DocumentStatus.failed
            document.error_reason = "No extractable text content"
            db.commit()
            return

        embedding_client = get_embedding_client(settings)
        vectors = embedding_client.embed_documents([c.content for c in chunks])
        vector_store = get_vector_store(settings, dimension=embedding_client.dimension)

        chunk_rows = []
        for chunk in chunks:
            row = Chunk(
                document_id=document.id,
                content=chunk.content,
                token_count=chunk.token_count,
                chunk_index=chunk.index,
                source="document",
                metadata_json={"filename": document.filename},
            )
            db.add(row)
            chunk_rows.append(row)
        db.flush()  # assign chunk_rows[i].id

        ids = [str(row.id) for row in chunk_rows]
        metadatas = [
            {
                "document_id": str(document.id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "filename": document.filename,
                "source": row.source,
            }
            for row in chunk_rows
        ]
        vector_store.upsert(ids=ids, vectors=vectors, metadatas=metadatas)

        for row, _id in zip(chunk_rows, ids):
            row.embedding_id = _id

        document.status = DocumentStatus.indexed
        document.indexed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Ingested document %s into %d chunks", document_id, len(chunk_rows))
    except Exception as exc:  # noqa: BLE001 - surfaced to the Documents UI
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = DocumentStatus.failed
            document.error_reason = str(exc)[:2000]
            db.commit()
        logger.exception("Ingestion failed for document %s", document_id)
        raise
    finally:
        db.close()


def save_upload(directory: str, filename: str, content: bytes) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path
