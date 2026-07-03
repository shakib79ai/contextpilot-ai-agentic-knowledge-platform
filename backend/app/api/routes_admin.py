import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_reviewer
from app.database import get_db
from app.models.enums import KnowledgeUpdateStatus
from app.models.review import KnowledgeUpdate
from app.models.user import User
from app.tasks.evaluation import run_eval_set_task
from context_learning.feedback_store import feedback_summary
from context_learning.learning_engine import apply_knowledge_update

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/knowledge-updates")
def list_knowledge_updates(
    status_filter: KnowledgeUpdateStatus | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_reviewer),
):
    query = db.query(KnowledgeUpdate)
    if status_filter is not None:
        query = query.filter(KnowledgeUpdate.status == status_filter)
    updates = query.order_by(KnowledgeUpdate.created_at.desc()).all()
    return [
        {
            "id": str(u.id),
            "source_document_id": str(u.source_document_id) if u.source_document_id else None,
            "chunk_id": str(u.chunk_id) if u.chunk_id else None,
            "proposed_content": u.proposed_content,
            "reason": u.reason,
            "status": u.status,
            "created_at": u.created_at,
        }
        for u in updates
    ]


@router.post("/knowledge-updates/{update_id}/approve")
def approve_knowledge_update(
    update_id: uuid.UUID,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer),
):
    update = db.get(KnowledgeUpdate, update_id)
    if update is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge update not found")

    update.status = KnowledgeUpdateStatus.approved
    update.reviewed_by = reviewer.id
    db.commit()

    apply_knowledge_update(db, update)
    db.refresh(update)
    return {"id": str(update.id), "status": update.status}


@router.post("/knowledge-updates/{update_id}/reject")
def reject_knowledge_update(
    update_id: uuid.UUID,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer),
):
    update = db.get(KnowledgeUpdate, update_id)
    if update is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge update not found")

    update.status = KnowledgeUpdateStatus.rejected
    update.reviewed_by = reviewer.id
    db.commit()
    return {"id": str(update.id), "status": update.status}


@router.get("/feedback-summary")
def get_feedback_summary(db: Session = Depends(get_db), _: User = Depends(require_reviewer)):
    return feedback_summary(db)


@router.post("/eval-runs")
def trigger_eval_run(dataset_path: str = "evals/test_cases/sample_eval_set.jsonl", _: User = Depends(require_reviewer)):
    task = run_eval_set_task.delay(dataset_path)
    return {"task_id": task.id, "dataset_path": dataset_path}
