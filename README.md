# ContextPilot AI: Production-Grade Multi-Agent Knowledge Learning Platform

ContextPilot AI is a production-style LLM application designed for enterprise knowledge management. It uses Retrieval-Augmented Generation, multi-agent orchestration, human-in-the-loop feedback, confidence scoring, and continuous context learning to help organizations maintain accurate and up-to-date knowledge bases.

The system is designed to answer enterprise questions with citations, evaluate its own confidence, learn from feedback, and escalate uncertain cases to humans instead of producing unreliable answers. It also includes autonomous knowledge update workflows where agents can identify outdated information, suggest changes, and improve the knowledge base over time.

This project demonstrates how a senior AI engineer would design and build an LLM system beyond a simple chatbot: scalable architecture, async processing, evaluation pipelines, observability, feedback loops, and production deployment readiness.

## Documentation

| Doc | Description |
|---|---|
| [REQUIREMENTS.md](REQUIREMENTS.md) | What you need installed/configured before running the project |
| [architecture.md](architecture.md) | High-level system architecture and component responsibilities |
| [system-design.md](system-design.md) | Data model, request lifecycle, sequence diagrams |
| [evaluation-framework.md](evaluation-framework.md) | Confidence scoring, RAGAS-style metrics, escalation logic |
| [human-in-the-loop.md](human-in-the-loop.md) | Review queue, escalation, reviewer workflow |
| [context-learning-engine.md](context-learning-engine.md) | How feedback becomes retrievable context over time |
| [deployment-guide.md](deployment-guide.md) | Local dev, Docker Compose, and cloud deployment |
| [visualizations/README.md](visualizations/README.md) | matplotlib scripts: eval report, threshold optimization, architecture diagram |

## Repository Layout

```
contextpilot-ai-agentic-knowledge-platform/
├── backend/            FastAPI app: routes, models, DB, Celery tasks
├── agents/             LangGraph multi-agent orchestration
├── rag_pipeline/        Chunking, embeddings, vector store, retrieval
├── evals/               Confidence scoring & evaluation framework
├── context_learning/    Feedback store & context learning engine
├── frontend/            Next.js UI (chat, upload, review dashboard)
├── infra/                Terraform stubs for cloud deployment
├── .github/workflows/    CI pipeline
└── docker-compose.yml    Local multi-service orchestration
```

## Core Capabilities

- **Multi-agent orchestration (LangGraph)** — Retriever, Answer, Evaluator, Knowledge Update, and Human Escalation agents cooperate through a typed shared state graph.
- **RAG pipeline** — Documents are chunked, embedded, stored in a pluggable vector store (FAISS by default; Pinecone/Weaviate adapters included), and retrieved with citations.
- **Confidence scoring & evaluation** — Every answer is scored on retrieval quality, source relevance, LLM self-check, and historical feedback before it is shown to a user.
- **Human-in-the-loop** — Low-confidence answers are routed to a review queue instead of being shown directly; reviewer decisions feed back into the learning engine.
- **Context learning engine** — Accepted answers, rejected answers, and reviewer corrections are stored and re-indexed so the system improves over time.
- **Async processing** — Document ingestion, evaluation, and learning jobs run on Celery workers backed by Redis so the API stays responsive.

## Quick Start (Local Development)

```bash
cp .env.example .env      # then edit .env and add your real API keys
docker-compose up --build
```

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Flower (Celery monitor): http://localhost:5555

See [deployment-guide.md](deployment-guide.md) for details, including running services individually without Docker.

## Technology Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Agent Orchestration:** LangChain, LangGraph
- **LLMs:** OpenAI GPT-4.1/GPT-4o, Anthropic Claude, or a local model — pluggable via `LLM_PROVIDER`
- **Vector Store:** FAISS (default, local), with Pinecone/Weaviate adapters
- **Database:** PostgreSQL
- **Cache/Queue:** Redis, Celery
- **Frontend:** Next.js / React
- **Monitoring:** LangSmith tracing hooks, Prometheus-friendly `/metrics`
- **Evaluation:** Custom RAGAS-style scoring (faithfulness, relevance, answer correctness)
- **Deployment:** Docker, Docker Compose, GitHub Actions CI, Terraform stubs for AWS ECS

## Security

This repository ships with **no real credentials**. `.env.example` contains clearly-labeled dummy placeholders (e.g. `sk-REPLACE_WITH_YOUR_OPENAI_API_KEY`). Copy it to `.env` and replace each placeholder with your own key before running the system against a real LLM provider. Never commit a populated `.env` file.

The app also **refuses to start** if `SECRET_KEY` is still the placeholder default and `APP_ENV` isn't `development` — that default is public (it's in this repo), so it must never sign real auth tokens. See [deployment-guide.md § Security Notes](deployment-guide.md#7-security-notes) for this and other hardening details (upload path handling, feedback role checks, conversation ownership, non-root container).

## License

MIT — see individual module headers for details.
