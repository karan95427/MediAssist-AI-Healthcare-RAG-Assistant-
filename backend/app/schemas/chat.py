from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceCitation(BaseModel):
    document: str
    page: int
    similarity: float
    snippet: str


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    mode: str
    sources: list[SourceCitation]


class ConversationRead(BaseModel):
    id: int
    question: str
    answer: str
    mode: str
    sources: list[SourceCitation]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClearHistoryResponse(BaseModel):
    deleted_count: int
    message: str

