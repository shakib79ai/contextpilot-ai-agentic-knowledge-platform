import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.router import api_router
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    from sqlalchemy import text

    from app.database import engine

    checks = {"database": "unknown"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001
        # Log the real error server-side only — this endpoint is
        # unauthenticated, so never echo raw exception/connection details back.
        logger.exception("readyz: database check failed")
        checks["database"] = "error"

    ok = all(v == "ok" for v in checks.values())
    return Response(
        content=str(checks),
        status_code=200 if ok else 503,
        media_type="text/plain",
    )


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
