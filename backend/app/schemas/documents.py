import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    filename: str
    status: str
    created_at: datetime


class DocumentListOut(BaseModel):
    items: list[DocumentOut]


class IngestionProgress(BaseModel):
    stage: str | None = None
    percent: int = 0


class IngestionJobOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    progress: IngestionProgress
    error: dict | None = None
    created_at: datetime
    updated_at: datetime


class UploadDocumentOut(BaseModel):
    document: DocumentOut
    ingestion_job: dict
