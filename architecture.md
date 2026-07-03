# Architecture Overview

ContextPilot AI is organized into eight cooperating layers. Each layer is independently testable and independently scalable.

## 1. User / Enterprise Interface

The Next.js frontend (`frontend/`) provides three surfaces:
- **Chat** — ask questions, see grounded answers with citations and a confidence badge.
- **Documents** — upload source material (PDF, Markdown, TXT) into the knowledge base.
- **Review Dashboard** — for human reviewers to resolve escalated, low-confidence answers.

## 2. API Gateway

`backend/app` is a FastAPI service that handles:
- JWT-based authentication (`backend/app/core/security.py`)
- Document upload (`POST /api/v1/documents`)
- Question answering (`POST /api/v1/query`)
- Feedback submission (`POST /api/v1/feedback`)
- Review queue management (`GET/POST /api/v1/review`)

All request/response contracts are defined as Pydantic schemas in `backend/app/schemas/`.

## 3. Agent Orchestration Layer (`agents/`)

Built with **LangGraph**. A single typed `AgentState` (see `agents/state.py`) flows through a directed graph of nodes:

```
        ┌────────────────┐
        │  Retriever      │  → finds top-k relevant chunks from the vector store
        │  Agent          │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Answer Agent    │  → generates a grounded response with citations
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Evaluator Agent │  → scores confidence (retrieval, relevance, self-check)
        └────────┬────────┘
                 │
         confidence >= auto-answer threshold?
           │yes                    │no
  ┌────────▼────────┐    ┌─────────▼──────────┐
  │ return answer     │    │ Human Escalation    │
  │ to user           │    │ Agent → review queue│
  └────────────────┘    └─────────────────────┘
                 │
        ┌────────▼─────────────┐
        │ Knowledge Update Agent │  → proposes KB updates from accepted/corrected answers
        └───────────────────────┘
```

Each agent is a plain Python callable (`agents/*_agent.py`) with a single `run(state) -> state` signature, making them independently unit-testable and swappable.

## 4. Context Learning Engine (`context_learning/`)

Stores every interaction outcome — accepted answers, rejected answers, reviewer corrections, and prompt/context adjustments — in the `feedback_events` and `knowledge_updates` tables. The `LearningEngine` periodically (via Celery beat) re-embeds high-value corrections and injects them back into the vector store as first-class, higher-priority context chunks.

## 5. RAG Pipeline (`rag_pipeline/`)

- `chunker.py` — token-aware document chunking with overlap
- `embeddings.py` — pluggable embedding client (OpenAI / local sentence-transformers)
- `vector_store.py` — `VectorStore` interface with `FAISSVectorStore`, `PineconeVectorStore`, `WeaviateVectorStore` implementations
- `ingestion.py` — orchestrates chunk → embed → upsert, run as a Celery task
- `retriever.py` — similarity search + metadata filtering + citation formatting

## 6. Evaluation & Confidence System (`evals/`)

Every answer receives a composite confidence score (0–1) from `evals/confidence_scoring.py`, combining:

| Signal | Weight | Source |
|---|---|---|
| Retrieval quality | 30% | vector similarity of top chunks |
| Source relevance | 20% | LLM-judged relevance of cited chunks to the question |
| Self-check | 30% | LLM asked to critique its own answer for unsupported claims |
| Historical feedback | 20% | acceptance rate of similar past answers |

See [evaluation-framework.md](evaluation-framework.md) for the full formula and calibration notes.

## 7. Human-in-the-Loop Review (`backend/app/api/routes_review.py`)

When confidence falls below `CONFIDENCE_ESCALATION_THRESHOLD`, the Human Escalation Agent creates a `ReviewTask` instead of returning the answer directly. Reviewers approve, edit, or reject the answer from the Review Dashboard; their decision is written back as a `FeedbackEvent` that the Context Learning Engine consumes.

## 8. Async Processing Layer

Celery (broker + result backend on Redis) runs:
- `tasks/indexing.py` — document ingestion (chunk/embed/upsert)
- `tasks/evaluation.py` — batch re-scoring and eval-set runs
- `tasks/learning.py` — periodic context-learning re-indexing (Celery beat)

This keeps the FastAPI request path fast — uploads and heavy evaluation runs are always asynchronous.
