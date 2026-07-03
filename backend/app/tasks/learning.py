from app.celery_app import celery_app


@celery_app.task(name="app.tasks.learning.run_maintenance_cycle")
def run_maintenance_cycle() -> dict:
    from app.database import SessionLocal
    from context_learning.learning_engine import find_stale_corrections

    db = SessionLocal()
    try:
        stale = find_stale_corrections(db)
        return {"stale_corrections_found": len(stale), "chunk_ids": [str(c.id) for c in stale]}
    finally:
        db.close()
