from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ClearHistoryResponse, ConversationRead
from app.schemas.document import DocumentDeleteResponse, DocumentRead, DocumentUploadResponse
from app.services.chat_service import ChatService
from app.services.upload_service import UploadService

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    document = UploadService(db).upload_document(current_user, file)
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        total_pages=document.total_pages,
        uploaded_at=document.uploaded_at,
        message="Document uploaded and indexed successfully.",
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    return ChatService(db).ask_question(current_user, payload.question)


@router.get("/history", response_model=list[ConversationRead])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationRead]:
    return ChatService(db).get_history(current_user)


@router.delete("/history", response_model=ClearHistoryResponse)
def clear_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClearHistoryResponse:
    deleted_count = ChatService(db).clear_history(current_user)
    return ClearHistoryResponse(deleted_count=deleted_count, message="Conversation history cleared.")


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentRead]:
    documents = UploadService(db).list_documents(current_user)
    return [DocumentRead.model_validate(document) for document in documents]


@router.delete("/document/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDeleteResponse:
    document = UploadService(db).delete_document(current_user, document_id)
    return DocumentDeleteResponse(id=document.id, message="Document deleted successfully.")

