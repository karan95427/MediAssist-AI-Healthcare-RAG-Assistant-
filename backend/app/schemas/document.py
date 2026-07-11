from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    id: int
    filename: str
    total_pages: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    total_pages: int
    uploaded_at: datetime
    message: str


class DocumentDeleteResponse(BaseModel):
    id: int
    message: str
