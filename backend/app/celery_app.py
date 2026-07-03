from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "contextpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.indexing", "app.tasks.evaluation", "app.tasks.learning"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    "context-learning-maintenance-cycle": {
        "task": "app.tasks.learning.run_maintenance_cycle",
        "schedule": 3600.0,  # hourly
    },
}
