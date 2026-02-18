import asyncio
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Document, IngestionJob
from app.schemas.documents import DocumentListOut, DocumentOut
from app.services.ingestion import run_ingestion
from app.settings import settings


router = APIRouter()


@router.post("")
async def upload_document(
    file: UploadFile,
    title: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF is supported")

    now = datetime.utcnow()
    doc = Document(
        title=title or file.filename,
        filename=file.filename,
        storage_path="",
        status="queued",
        created_at=now,
        updated_at=now,
    )
    session.add(doc)
    await session.flush()

    doc_dir = Path(settings.upload_dir) / str(doc.id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    storage_path = str(doc_dir / file.filename)
    await _save_upload(file, storage_path)

    doc.storage_path = storage_path
    doc.updated_at = now

    job = IngestionJob(document_id=doc.id, status="queued", stage=None, percent=0, created_at=now, updated_at=now)
    session.add(job)
    await session.commit()

    asyncio.create_task(run_ingestion(str(job.id)))

    return {
        "document": DocumentOut.model_validate(doc, from_attributes=True).model_dump(),
        "ingestion_job": {"id": str(job.id), "status": job.status},
    }


@router.get("")
async def list_documents(session: AsyncSession = Depends(get_session)) -> dict:
    rows = (await session.execute(select(Document).order_by(Document.created_at.desc()))).scalars().all()
    return DocumentListOut(items=[DocumentOut.model_validate(x, from_attributes=True) for x in rows]).model_dump()


@router.get("/{document_id}")
async def get_document(document_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    doc = await session.get(Document, uuid.UUID(document_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc, from_attributes=True).model_dump()


@router.delete("/{document_id}")
async def delete_document(document_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    doc = await session.get(Document, uuid.UUID(document_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await session.delete(doc)
    await session.commit()

    doc_dir = Path(settings.upload_dir) / str(document_id)
    if doc_dir.exists():
        shutil.rmtree(doc_dir, ignore_errors=True)

    return {"deleted": True}


@router.post("/{document_id}/reindex")
async def reindex_document(document_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    doc = await session.get(Document, uuid.UUID(document_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    now = datetime.utcnow()
    doc.status = "queued"
    doc.updated_at = now
    job = IngestionJob(document_id=doc.id, status="queued", stage=None, percent=0, created_at=now, updated_at=now)
    session.add(job)
    await session.commit()
    asyncio.create_task(run_ingestion(str(job.id)))
    return {"ingestion_job": {"id": str(job.id), "status": job.status}}


async def _save_upload(upload: UploadFile, dest_path: str) -> None:
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
