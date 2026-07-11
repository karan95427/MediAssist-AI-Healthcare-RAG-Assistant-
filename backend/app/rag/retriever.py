from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import get_settings
from app.rag.embedding_service import EmbeddingService
from app.rag.router import QueryMode
from app.rag.vector_store import SearchResult, VectorStoreService

settings = get_settings()
MIN_SIMILARITY = 0.35


@dataclass(slots=True)
class RetrievedChunk:
    text: str
    similarity: float
    page_number: int
    source_document: str
    source_type: str


class Retriever:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStoreService) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(self, question: str, mode: QueryMode, user_id: int | None = None) -> list[RetrievedChunk]:
        query_embedding = self.embedding_service.embed_query(question)
        namespace = "faq" if mode == QueryMode.FAQ or user_id is None else f"user_{user_id}"
        results = self.vector_store.search(namespace, query_embedding, settings.retrieval_top_k)
        filtered_results = [result for result in results if result.similarity >= MIN_SIMILARITY]
        return [self._to_retrieved_chunk(result) for result in filtered_results]

    @staticmethod
    def _to_retrieved_chunk(result: SearchResult) -> RetrievedChunk:
        return RetrievedChunk(
            text=result.chunk.text,
            similarity=result.similarity,
            page_number=result.chunk.page_number,
            source_document=result.chunk.document_name,
            source_type=result.chunk.source_type,
        )
