# Deployment Guide

## 1. Local Development (Docker Compose — recommended)

```bash
cp .env.example .env         # edit .env with real API keys before using a live LLM
docker-compose up --build
```

This starts: `postgres`, `redis`, `backend` (FastAPI), `worker` (Celery), `beat` (Celery beat scheduler), `flower` (Celery monitoring UI), and `frontend` (Next.js).

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Flower: http://localhost:5555

Run migrations (first time only, or after a model change):

```bash
docker-compose exec backend alembic upgrade head
```

Register a user via the frontend or `POST /api/v1/auth/register`, then promote it to reviewer/admin so it can access the Review Dashboard and admin endpoints — role escalation is intentionally a CLI/ops action, not an API endpoint:

```bash
docker-compose exec backend python scripts/promote_user.py --email you@example.com --role admin
```

## 2. Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal, from backend/)
celery -A app.celery_app worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

You'll need local Postgres and Redis instances (or point `DATABASE_URL`/`REDIS_URL` at hosted ones). With `VECTOR_STORE_PROVIDER=faiss` (the default), no external vector DB is required — FAISS persists to `VECTOR_STORE_DIR` on disk.

## 3. Running the Evaluation Suite

```bash
cd backend
python -m evals.run_eval --dataset ../evals/test_cases/sample_eval_set.jsonl
```

## 4. Production Deployment (AWS ECS/EKS via Terraform)

`infra/` contains Terraform stubs for:
- an ECS Fargate service for the FastAPI backend and Celery workers,
- an RDS Postgres instance,
- an ElastiCache Redis cluster,
- an S3 bucket for uploaded documents,
- Secrets Manager entries for `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `PINECONE_API_KEY`, etc. (populate these with real values — never commit them).

```bash
cd infra
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

Container images are built and pushed by `.github/workflows/ci.yml` on merge to `main`; wire in your registry (ECR) and cluster details in the workflow's `env:` block before enabling the deploy job.

## 5. Swapping in Real Credentials

Every credential in `.env.example` is a clearly-labeled dummy value (`REPLACE_WITH_...`). Before any real deployment:

1. Copy `.env.example` → `.env` (local) or populate your secrets manager (production).
2. Replace each `REPLACE_WITH_...` placeholder with a real key.
3. Never commit `.env` — it's already covered by `.gitignore`.
4. Rotate keys immediately if one is ever accidentally committed.

## 6. Health & Readiness

- `GET /healthz` — liveness (process up)
- `GET /readyz` — readiness (DB + Redis + vector store reachable)
- `GET /metrics` — Prometheus-format metrics for scraping into Grafana
