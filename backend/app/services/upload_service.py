from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.rag.pdf_parser import PDFParser
from app.rag.text_chunker import TextChunker
from app.services.chat_service import get_runtime_services

logger = logging.getLogger(__name__)
settings = get_settings()


class UploadService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pdf_parser = PDFParser()
        self.chunker = TextChunker(settings.chunk_size_words, settings.chunk_overlap_words)
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def upload_document(self, user: User, file: UploadFile) -> UploadedDocument:
        self._validate_upload(file)
        file_bytes = file.file.read()
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(file_bytes) > max_size_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 20 MB limit.")

        user_dir = self.upload_dir / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{uuid4().hex}_{file.filename}"
        file_path = user_dir / stored_filename
        file_path.write_bytes(file_bytes)

        try:
            pages = self.pdf_parser.parse(file_path)
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            logger.exception("Failed to parse uploaded document %s", file.filename)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unable to parse PDF: {exc}") from exc

        if not pages:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The uploaded PDF did not contain extractable text.")

        document = UploadedDocument(
            user_id=user.id,
            filename=file.filename or "uploaded_document.pdf",
            stored_filename=stored_filename,
            file_path=str(file_path),
            total_pages=max(page.page_number for page in pages),
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        chunks = self.chunker.chunk_pages(
            pages=pages,
            document_name=document.filename,
            source_type="uploaded_document",
            user_id=user.id,
            document_id=document.id,
        )
        runtime = get_runtime_services()
        embeddings = runtime.embedding_service.embed_texts([chunk.text for chunk in chunks])
        runtime.vector_store.add_uploaded_document(user.id, chunks, embeddings)
        logger.info("Indexed uploaded document %s for user %s", document.filename, user.id)
        return document

    def list_documents(self, user: User) -> list[UploadedDocument]:
        query = select(UploadedDocument).where(UploadedDocument.user_id == user.id).order_by(UploadedDocument.uploaded_at.desc())
        return list(self.db.scalars(query).all())

    def delete_document(self, user: User, document_id: int) -> UploadedDocument:
        document = self.db.scalar(
            select(UploadedDocument).where(UploadedDocument.id == document_id, UploadedDocument.user_id == user.id)
        )
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        Path(document.file_path).unlink(missing_ok=True)
        get_runtime_services().vector_store.remove_document(user.id, document.id)
        self.db.delete(document)
        self.db.commit()
        logger.info("Deleted uploaded document %s for user %s", document.filename, user.id)
        return document

    @staticmethod
    def _validate_upload(file: UploadFile) -> None:
        filename = (file.filename or "").lower()
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported.")
        if file.content_type not in {"application/pdf", "application/octet-stream", None}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type.")
