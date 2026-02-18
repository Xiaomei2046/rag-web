import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LlmConfig(BaseModel):
    provider: str
    model: str = ""
    temperature: float = 0.2


class RetrievalConfig(BaseModel):
    top_k: int = 5


class CreateMessageIn(BaseModel):
    content: str
    document_ids: list[str] = Field(default_factory=list)
    llm: LlmConfig
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict] = Field(default_factory=list)
    usage: dict = Field(default_factory=dict)
    created_at: datetime


class CreateMessageOut(BaseModel):
    message: MessageOut


class CreateSessionIn(BaseModel):
    title: str = "Untitled"


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime


class SessionListOut(BaseModel):
    items: list[SessionOut]


class SessionDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    messages: list[MessageOut]
