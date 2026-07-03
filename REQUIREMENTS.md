# Requirements

What you need before running ContextPilot AI.

## Option A: Docker (recommended)

- Docker Desktop / Docker Engine 24+ with Compose v2 (`docker compose version`)
- ~4 GB free disk space (Postgres, Redis, model deps, Node build)

That's it — Postgres, Redis, and both apps run as containers.

## Option B: Running services natively (no Docker)

- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL 16
- Redis 7

## API keys

None are required to run the system — it works fully offline out of the box (deterministic local embeddings + extractive answers, see `.env.example`). Add real keys only when you want live LLM-generated answers:

| Key | Required? | Where to get it |
|---|---|---|
| `OPENAI_API_KEY` | Optional | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | Optional (alternative to OpenAI, set `LLM_PROVIDER=anthropic`) | https://console.anthropic.com/settings/keys |
| `PINECONE_API_KEY` | Optional (only if `VECTOR_STORE_PROVIDER=pinecone`) | https://app.pinecone.io |
| `WEAVIATE_API_KEY` | Optional (only if `VECTOR_STORE_PROVIDER=weaviate`) | your Weaviate instance |
| `LANGSMITH_API_KEY` | Optional (tracing/observability) | https://smith.langchain.com |

Copy `.env.example` to `.env` and fill in whichever of these you're using; leave the rest as the dummy placeholders.

## Ports used

| Port | Service |
|---|---|
| 3000 | Frontend (Next.js) |
| 8000 | Backend API (FastAPI) |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 5555 | Flower (Celery monitor) |

## First run checklist

1. `cp .env.example .env`
2. `docker-compose up --build` (or see [deployment-guide.md](deployment-guide.md) for running natively)
3. Register a user at http://localhost:3000/login
4. `docker-compose exec backend python scripts/promote_user.py --email you@example.com --role admin` (needed to access the Review Dashboard)
