FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /repo

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Copy the whole repo (not just backend/) so the top-level agents/,
# rag_pipeline/, evals/, and context_learning/ packages are available.
COPY . .

# Run as a non-root user (defense in depth — limits blast radius of any
# file-write bug regardless of what path validation exists in app code).
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /repo/data/vector_store /repo/data/uploads \
    && chown -R appuser:appuser /repo

USER appuser
WORKDIR /repo/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
