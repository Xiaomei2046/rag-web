import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import IngestionJob


router = APIRouter()


@router.get("/{job_id}")
async def get_ingestion_job(job_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    job = await session.get(IngestionJob, uuid.UUID(job_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": str(job.id),
        "document_id": str(job.document_id),
        "status": job.status,
        "progress": {"stage": job.stage, "percent": job.percent},
        "error": None if not job.error_message else {"code": job.error_code, "message": job.error_message},
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
