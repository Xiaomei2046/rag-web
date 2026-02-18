import uuid
from datetime import datetime
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ChatMessage, ChatSession
from app.schemas.chat import (
    CreateMessageIn,
    CreateMessageOut,
    CreateSessionIn,
    SessionDetailOut,
    SessionListOut,
    SessionOut,
)
from app.services.rag import answer_with_rag
from app.services.retrieval import retrieve_chunks


router = APIRouter()


@router.post("/sessions")
async def create_session(payload: CreateSessionIn, session: AsyncSession = Depends(get_session)) -> dict:
    now = datetime.utcnow()
    s = ChatSession(title=payload.title, created_at=now)
    session.add(s)
    await session.commit()
    return SessionOut.model_validate(s, from_attributes=True).model_dump()


@router.get("/sessions")
async def list_sessions(session: AsyncSession = Depends(get_session)) -> dict:
    rows = (await session.execute(select(ChatSession).order_by(ChatSession.created_at.desc()))).scalars().all()
    return SessionListOut(items=[SessionOut.model_validate(x, from_attributes=True) for x in rows]).model_dump()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    s = await session.get(ChatSession, uuid.UUID(session_id))
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    msgs = (
        await session.execute(
            select(ChatMessage).where(ChatMessage.session_id == s.id).order_by(ChatMessage.created_at.asc())
        )
    ).scalars().all()
    return SessionDetailOut(
        id=s.id,
        title=s.title,
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "usage": m.usage,
                "created_at": m.created_at,
            }
            for m in msgs
        ],
    ).model_dump()


@router.post("/sessions/{session_id}/messages")
async def create_message(
    session_id: str,
    payload: CreateMessageIn,
    session: AsyncSession = Depends(get_session),
) -> dict:
    s = await session.get(ChatSession, uuid.UUID(session_id))
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.utcnow()
    user_msg = ChatMessage(session_id=s.id, role="user", content=payload.content, citations=[], usage={}, created_at=now)
    session.add(user_msg)
    await session.commit()

    t0 = perf_counter()
    retrieved = await retrieve_chunks(
        session,
        query=payload.content,
        top_k=payload.retrieval.top_k,
        document_ids=payload.document_ids or None,
    )
    t1 = perf_counter()

    result = await answer_with_rag(
        provider=payload.llm.provider,
        model=payload.llm.model,
        question=payload.content,
        retrieved=retrieved,
        temperature=payload.llm.temperature,
    )
    t2 = perf_counter()

    citations = [
        {
            "chunk_id": str(item["chunk"].id),
            "document_id": str(item["chunk"].document_id),
            "doc_title": item["doc_title"],
            "page_start": int(item["chunk"].page_start),
            "page_end": int(item["chunk"].page_end),
            "snippet": str(item["chunk"].content)[:320],
            "score": max(0.0, 1.0 - float(item["distance"])),
        }
        for item in retrieved
    ]

    assistant_msg = ChatMessage(
        session_id=s.id,
        role="assistant",
        content=result.content,
        citations=citations,
        llm_provider=payload.llm.provider,
        llm_model=payload.llm.model,
        usage={
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
            "latency_ms": {
                "retrieval": int((t1 - t0) * 1000),
                "llm": int((t2 - t1) * 1000),
                "total": int((t2 - t0) * 1000),
            },
        },
        created_at=datetime.utcnow(),
    )
    session.add(assistant_msg)
    await session.commit()

    return CreateMessageOut(
        message={
            "id": assistant_msg.id,
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            "citations": assistant_msg.citations,
            "usage": assistant_msg.usage,
            "created_at": assistant_msg.created_at,
        }
    ).model_dump()
