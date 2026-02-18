import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.embeddings import embed_texts
from app.models import Chunk, Document


async def retrieve_chunks(
    session: AsyncSession,
    *,
    query: str,
    top_k: int,
    document_ids: list[str] | None,
) -> list[dict]:
    embedding = (await embed_texts([query])).vectors[0]

    stmt: Select = (
        select(
            Chunk,
            Document.title.label("doc_title"),
            Chunk.embedding.cosine_distance(embedding).label("distance"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.embedding.is_not(None))
    )
    if document_ids:
        ids = [uuid.UUID(x) for x in document_ids]
        stmt = stmt.where(Chunk.document_id.in_(ids))
    stmt = stmt.order_by("distance").limit(top_k)
    rows = (await session.execute(stmt)).all()
    return [
        {
            "chunk": row[0],
            "doc_title": str(row[1]),
            "distance": float(row[2]),
        }
        for row in rows
    ]
