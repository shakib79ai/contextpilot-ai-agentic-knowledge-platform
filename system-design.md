# System Design

## Data Model

```
User(id, email, hashed_password, role, created_at)

Document(id, owner_id, filename, content_type, status, uploaded_at)
Chunk(id, document_id, content, token_count, embedding_id, metadata_json)

Conversation(id, user_id, created_at)
Message(id, conversation_id, role, content, created_at)

Answer(id, message_id, content, confidence_score, status, citations_json, created_at)
  status ∈ {auto_answered, escalated, reviewed_approved, reviewed_edited, reviewed_rejected}

FeedbackEvent(id, answer_id, user_id, kind, comment, created_at)
  kind ∈ {thumbs_up, thumbs_down, reviewer_approve, reviewer_edit, reviewer_reject}

ReviewTask(id, answer_id, assigned_to, status, priority, created_at, resolved_at)
  status ∈ {pending, in_review, resolved}

KnowledgeUpdate(id, source_document_id, chunk_id, proposed_content, reason,
                status, created_by_agent, reviewed_by, created_at)
  status ∈ {proposed, approved, rejected, applied}
```

Postgres is the system of record; the vector store holds only embeddings + a foreign key back to `Chunk.id` so it can always be rebuilt from Postgres.

## Request Lifecycle: `POST /api/v1/query`

1. **API Gateway** authenticates the request, persists the `Message`, and invokes the agent graph synchronously (typical latency budget: 2–6s).
2. **Retriever Agent** embeds the question and performs top-k similarity search against the vector store, returning chunks + similarity scores.
3. **Answer Agent** calls the LLM with the question + retrieved context, producing a grounded answer with inline citation markers.
4. **Evaluator Agent** computes the composite confidence score (see [evaluation-framework.md](evaluation-framework.md)).
5. **Decision point:**
   - `confidence >= CONFIDENCE_AUTO_ANSWER_THRESHOLD` → `Answer.status = auto_answered`, content returned directly.
   - `confidence < CONFIDENCE_ESCALATION_THRESHOLD` → **Human Escalation Agent** creates a `ReviewTask`; the answer content is **withheld** from the API response (`status = escalated`, `pending_review = true`) until a reviewer resolves it.
   - In between → answer content is returned but flagged `low_confidence` in the UI, and a low-priority `ReviewTask` is created for async audit.
6. Response is persisted and returned to the client with the answer, citations, and confidence score.

## Document Ingestion Lifecycle

1. `POST /api/v1/documents` stores the raw file and creates a `Document(status=pending)` row, then enqueues `tasks.indexing.ingest_document`.
2. The Celery worker chunks the document, generates embeddings, and upserts vectors, updating `Document.status = indexed` and writing `Chunk` rows.
3. Ingestion failures set `status = failed` with an error reason surfaced in the Documents UI.

## Knowledge Update Lifecycle

1. Whenever a `ReviewTask` is resolved with `reviewer_edit`, the **Knowledge Update Agent** diff's the reviewer's correction against the original cited chunk(s).
2. If the diff represents a factual correction (not just style), it creates a `KnowledgeUpdate(status=proposed)`.
3. A second reviewer (or an auto-approve rule for high-trust sources) sets `status = approved`, which triggers `tasks.learning.apply_knowledge_update`, re-embedding the corrected content and marking the update `applied`.

## Scalability Notes

- The FastAPI process is stateless; horizontal scaling is a simple replica count change (see `deployment-guide.md`).
- All heavy work (ingestion, batch evals, learning re-indexing) is offloaded to Celery workers, which scale independently by queue.
- The vector store abstraction (`rag_pipeline/vector_store.py`) allows moving from local FAISS to a managed service (Pinecone/Weaviate) without touching agent or API code.
- Redis is used both as the Celery broker and as a response cache for repeated identical queries (keyed on a hash of the normalized question + top document IDs).
