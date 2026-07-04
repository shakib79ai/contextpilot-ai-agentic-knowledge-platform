import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.tasks.indexing import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])

# Maps content-type -> the storage extension we use on disk. Deriving the
# on-disk filename from this fixed mapping (rather than the client-supplied
# filename) is what prevents path traversal — the client's filename is only
# ever used for display (Document.filename), never for building a path.
ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from rag_pipeline.ingestion import save_upload

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    settings = get_settings()
    content = await file.read()
    document_id = uuid.uuid4()
    # Never build the storage path from the client-supplied filename — build
    # it entirely from server-controlled values (see ALLOWED_CONTENT_TYPES).
    safe_filename = f"{document_id}{ALLOWED_CONTENT_TYPES[file.content_type]}"
    storage_path = save_upload(settings.upload_dir, safe_filename, content)

    document = Document(
        id=document_id,
        owner_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type,
        storage_path=storage_path,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    ingest_document_task.delay(str(document.id))
    return document


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Document).filter(Document.owner_id == current_user.id).order_by(Document.uploaded_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if document is None or document.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document
