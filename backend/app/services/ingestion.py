import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy import delete, select

from app.db import async_session_factory
from app.llm.embeddings import embed_texts
from app.models import Chunk, Document, DocumentPage, IngestionJob


def utcnow() -> datetime:
    return datetime.utcnow()


async def _set_job(job: IngestionJob, *, status: str | None = None, stage: str | None = None, percent: int | None = None) -> None:
    if status is not None:
        job.status = status
    if stage is not None:
        job.stage = stage
    if percent is not None:
        job.percent = percent
    job.updated_at = utcnow()


async def run_ingestion(job_id: str) -> None:
    async with async_session_factory() as session:
        job_uuid = uuid.UUID(job_id)
        job = await session.get(IngestionJob, job_uuid)
        if job is None:
            return
        document = await session.get(Document, job.document_id)
        if document is None:
            return

        try:
            await _set_job(job, status="processing", stage="extract", percent=0)
            document.status = "processing"
            document.updated_at = utcnow()
            await session.commit()

            await session.execute(delete(DocumentPage).where(DocumentPage.document_id == document.id))
            await session.execute(delete(Chunk).where(Chunk.document_id == document.id))
            await session.commit()

            pages = _extract_pdf_pages(document.storage_path)
            for p in pages:
                session.add(
                    DocumentPage(
                        document_id=document.id,
                        page_number=p["page_number"],
                        text=p["text"],
                        created_at=utcnow(),
                    )
                )
            await session.commit()

            await _set_job(job, stage="chunk", percent=25)
            await session.commit()

            chunks = _chunk_pages(pages)
            for c in chunks:
                session.add(
                    Chunk(
                        document_id=document.id,
                        page_start=c["page_start"],
                        page_end=c["page_end"],
                        content=c["content"],
                        metadata_=c["metadata"],
                        embedding=None,
                        embedding_model=None,
                        created_at=utcnow(),
                    )
                )
            await session.commit()

            await _set_job(job, stage="embed", percent=50)
            await session.commit()

            chunk_rows = (
                await session.execute(select(Chunk).where(Chunk.document_id == document.id).order_by(Chunk.page_start, Chunk.id))
            ).scalars().all()

            batch_size = 64
            for i in range(0, len(chunk_rows), batch_size):
                batch = chunk_rows[i : i + batch_size]
                texts = [x.content for x in batch]
                result = await embed_texts(texts)
                for row, vec in zip(batch, result.vectors, strict=True):
                    row.embedding = vec
                    row.embedding_model = result.model
                await session.commit()
                await asyncio.sleep(0)

            await _set_job(job, stage="store", percent=90)
            document.status = "completed"
            document.updated_at = utcnow()
            await _set_job(job, status="completed", percent=100)
            await session.commit()
        except Exception as e:
            job = await session.get(IngestionJob, job_id)
            if job is not None:
                await _set_job(job, status="failed", percent=100)
                job.error_code = "INGESTION_FAILED"
                job.error_message = str(e)
            document = await session.get(Document, job.document_id) if job is not None else None
            if document is not None:
                document.status = "failed"
                document.updated_at = utcnow()
            await session.commit()


def _extract_pdf_pages(storage_path: str) -> list[dict[str, Any]]:
    path = Path(storage_path)
    reader = PdfReader(str(path))
    pages: list[dict[str, Any]] = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": idx, "text": text})
    return pages


def _chunk_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks: list[dict[str, Any]] = []
    for p in pages:
        page_number = int(p["page_number"])
        text = str(p["text"]).strip()
        if not text:
            continue
        parts = splitter.split_text(text)
        for part in parts:
            content = part.strip()
            if not content:
                continue
            chunks.append(
                {
                    "page_start": page_number,
                    "page_end": page_number,
                    "content": content,
                    "metadata": {"page_number": page_number},
                }
            )
    return chunks
