from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import threading

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.conversation import Conversation
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.rag.embedding_service import EmbeddingService
from app.rag.llm_service import LLMService
from app.rag.pdf_parser import PDFParser, ParsedPage
from app.rag.retriever import RetrievedChunk, Retriever
from app.rag.router import QueryMode, QueryRouter
from app.rag.text_chunker import TextChunker
from app.rag.vector_store import VectorStoreService
from app.schemas.chat import ChatResponse, ConversationRead, SourceCitation

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(slots=True)
class RuntimeServices:
    embedding_service: EmbeddingService
    vector_store: VectorStoreService
    retriever: Retriever
    query_router: QueryRouter
    llm_service: LLMService


_runtime_services: RuntimeServices | None = None
_refresh_lock = threading.Lock()
_refresh_started = False


def initialize_knowledge_base() -> None:
    runtime = get_runtime_services()
    if _can_use_cached_curated_index(runtime.vector_store):
        logger.info("Loaded cached curated FAQ knowledge base with %s chunks", runtime.vector_store.faq_chunk_count())
        return

    chunker = TextChunker(settings.chunk_size_words, settings.chunk_overlap_words)
    pdf_parser = PDFParser()
    chunks = []

    for file_path in Path(settings.knowledge_base_dir).rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() == ".pdf":
            pages = pdf_parser.parse(file_path)
        else:
            text = file_path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            pages = [ParsedPage(page_number=1, text=text)]

        chunks.extend(
            chunker.chunk_pages(
                pages=pages,
                document_name=file_path.name,
                source_type=file_path.parent.name,
            )
        )

    embeddings = runtime.embedding_service.embed_texts([chunk.text for chunk in chunks])
    runtime.vector_store.build_index("faq", chunks, embeddings)
    logger.info("Curated FAQ knowledge base initialized with %s chunks", len(chunks))


def schedule_knowledge_base_refresh() -> None:
    global _refresh_started
    with _refresh_lock:
        if _refresh_started:
            return
        _refresh_started = True

    thread = threading.Thread(target=_refresh_knowledge_base_worker, name="knowledge-base-refresh", daemon=True)
    thread.start()


def _refresh_knowledge_base_worker() -> None:
    try:
        initialize_knowledge_base()
    except Exception:
        logger.exception("Background knowledge-base refresh failed")


def _can_use_cached_curated_index(vector_store: VectorStoreService) -> bool:
    metadata_path = Path(settings.faiss_index_path) / "faq.json"
    if not metadata_path.exists():
        return False
    if not vector_store.load_index("faq"):
        return False

    collection = vector_store._collections["faq"]
    if any(chunk.document_name.endswith(".csv") for chunk in collection.chunks):
        return False

    source_paths = [path for path in Path(settings.knowledge_base_dir).rglob("*") if path.is_file()]
    cached_documents = {chunk.document_name for chunk in collection.chunks}
    expected_documents = {path.name for path in source_paths}
    if expected_documents - cached_documents:
        return False

    latest_source_mtime = max((path.stat().st_mtime for path in source_paths), default=0)
    if latest_source_mtime > metadata_path.stat().st_mtime:
        return False
    return True


def get_runtime_services() -> RuntimeServices:
    global _runtime_services
    if _runtime_services is None:
        embedding_service = EmbeddingService(settings.embedding_model_name)
        vector_store = VectorStoreService(settings.faiss_index_path, embedding_service.dimension)
        vector_store.load_index("faq")
        _runtime_services = RuntimeServices(
            embedding_service=embedding_service,
            vector_store=vector_store,
            retriever=Retriever(embedding_service, vector_store),
            query_router=QueryRouter(),
            llm_service=LLMService(),
        )
    return _runtime_services


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.runtime = get_runtime_services()
        schedule_knowledge_base_refresh()

    def ask_question(self, user: User, question: str) -> ChatResponse:
        has_documents = self._user_has_documents(user.id)
        decision = self.runtime.query_router.route(question, has_documents)

        retrieved: list[RetrievedChunk] = []
        if decision.mode == QueryMode.DOCUMENT:
            retrieved = self.runtime.retriever.retrieve(
                question=question,
                mode=QueryMode.DOCUMENT,
                user_id=user.id,
            )

        answer = self.runtime.llm_service.answer_question(question, retrieved)
        sources = [self._to_source(chunk) for chunk in retrieved]
        conversation = Conversation(
            user_id=user.id,
            question=question,
            answer=answer,
            mode=decision.mode.value,
            sources_json=json.dumps([source.model_dump() for source in sources]),
        )
        self.db.add(conversation)
        self.db.commit()

        return ChatResponse(answer=answer, mode=decision.mode.value, sources=sources)

    def get_history(self, user: User) -> list[ConversationRead]:
        query = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at.desc())
        conversations = list(self.db.scalars(query).all())
        return [
            ConversationRead(
                id=conversation.id,
                question=conversation.question,
                answer=conversation.answer,
                mode=conversation.mode,
                sources=[SourceCitation(**item) for item in json.loads(conversation.sources_json)],
                created_at=conversation.created_at,
            )
            for conversation in conversations
        ]

    def clear_history(self, user: User) -> int:
        result = self.db.execute(delete(Conversation).where(Conversation.user_id == user.id))
        self.db.commit()
        return result.rowcount or 0

    def list_documents(self, user: User) -> list[UploadedDocument]:
        query = select(UploadedDocument).where(UploadedDocument.user_id == user.id).order_by(UploadedDocument.uploaded_at.desc())
        return list(self.db.scalars(query).all())

    def _user_has_documents(self, user_id: int) -> bool:
        db_result = self.db.scalar(select(UploadedDocument.id).where(UploadedDocument.user_id == user_id).limit(1))
        if db_result is None:
            return False
        return self.runtime.vector_store.has_user_documents(user_id)

    @staticmethod
    def _to_source(chunk: RetrievedChunk) -> SourceCitation:
        return SourceCitation(
            document=chunk.source_document,
            page=chunk.page_number,
            similarity=round(chunk.similarity, 4),
            snippet=chunk.text[:280].strip(),
        )

