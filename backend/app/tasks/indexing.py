import uuid

from app.celery_app import celery_app


@celery_app.task(name="app.tasks.indexing.ingest_document_task", bind=True, max_retries=3, default_retry_delay=30)
def ingest_document_task(self, document_id: str):
    from rag_pipeline.ingestion import ingest_document

    try:
        ingest_document(uuid.UUID(document_id))
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)
