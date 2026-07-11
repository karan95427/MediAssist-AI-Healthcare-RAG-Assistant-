from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from app.rag.text_chunker import TextChunk

logger = logging.getLogger(__name__)

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None


@dataclass(slots=True)
class SearchResult:
    chunk: TextChunk
    similarity: float


@dataclass(slots=True)
class NamespaceCollection:
    namespace: str
    chunks: list[TextChunk]
    embeddings: np.ndarray
    index: Any | None


class VectorStoreService:
    def __init__(self, storage_dir: str, embedding_dimension: int) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_dimension = embedding_dimension
        self._collections: dict[str, NamespaceCollection] = {}

    def build_index(self, namespace: str, chunks: list[TextChunk], embeddings: np.ndarray) -> None:
        self._collections[namespace] = NamespaceCollection(
            namespace=namespace,
            chunks=chunks,
            embeddings=embeddings.astype(np.float32),
            index=self._create_index(embeddings),
        )
        self.save_index(namespace)

    def load_index(self, namespace: str) -> bool:
        metadata_path = self.storage_dir / f"{namespace}.json"
        embeddings_path = self.storage_dir / f"{namespace}.npy"
        index_path = self.storage_dir / f"{namespace}.faiss"
        if not metadata_path.exists() or not embeddings_path.exists():
            return False

        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunks = [TextChunk(**item) for item in payload]
        embeddings = np.load(embeddings_path).astype(np.float32)
        index = None
        if faiss is not None and index_path.exists():
            index = faiss.read_index(str(index_path))
        elif len(embeddings):
            index = self._create_index(embeddings)

        self._collections[namespace] = NamespaceCollection(namespace=namespace, chunks=chunks, embeddings=embeddings, index=index)
        return True

    def save_index(self, namespace: str) -> None:
        collection = self._collections[namespace]
        metadata_path = self.storage_dir / f"{namespace}.json"
        embeddings_path = self.storage_dir / f"{namespace}.npy"
        index_path = self.storage_dir / f"{namespace}.faiss"

        metadata_path.write_text(json.dumps([asdict(chunk) for chunk in collection.chunks], indent=2), encoding="utf-8")
        np.save(embeddings_path, collection.embeddings)

        if faiss is not None and collection.index is not None:
            faiss.write_index(collection.index, str(index_path))

    def add_uploaded_document(self, user_id: int, chunks: list[TextChunk], embeddings: np.ndarray) -> None:
        namespace = self._user_namespace(user_id)
        existing = self._collections.get(namespace)
        if existing is None and not self.load_index(namespace):
            self.build_index(namespace, chunks, embeddings)
            return

        existing = self._collections[namespace]
        combined_chunks = [*existing.chunks, *chunks]
        combined_embeddings = embeddings if existing.embeddings.size == 0 else np.vstack([existing.embeddings, embeddings]).astype(np.float32)
        self._collections[namespace] = NamespaceCollection(
            namespace=namespace,
            chunks=combined_chunks,
            embeddings=combined_embeddings,
            index=self._create_index(combined_embeddings),
        )
        self.save_index(namespace)

    def remove_document(self, user_id: int, document_id: int) -> None:
        namespace = self._user_namespace(user_id)
        collection = self._collections.get(namespace)
        if collection is None and not self.load_index(namespace):
            return

        collection = self._collections[namespace]
        keep_indexes = [index for index, chunk in enumerate(collection.chunks) if chunk.document_id != document_id]
        filtered_chunks = [collection.chunks[index] for index in keep_indexes]
        if keep_indexes:
            filtered_embeddings = collection.embeddings[keep_indexes].astype(np.float32)
        else:
            filtered_embeddings = np.empty((0, self.embedding_dimension), dtype=np.float32)

        self._collections[namespace] = NamespaceCollection(
            namespace=namespace,
            chunks=filtered_chunks,
            embeddings=filtered_embeddings,
            index=self._create_index(filtered_embeddings),
        )
        self.save_index(namespace)

    def search(self, namespace: str, query_embedding: np.ndarray, top_k: int) -> list[SearchResult]:
        collection = self._collections.get(namespace)
        if collection is None and not self.load_index(namespace):
            return []

        collection = self._collections[namespace]
        if not collection.chunks:
            return []

        query = np.asarray([query_embedding], dtype=np.float32)
        if faiss is not None and collection.index is not None:
            scores, indexes = collection.index.search(query, min(top_k, len(collection.chunks)))
            return self._materialize_results(collection, scores[0], indexes[0])

        similarities = np.dot(collection.embeddings, query_embedding)
        top_indexes = np.argsort(similarities)[::-1][:top_k]
        return [SearchResult(chunk=collection.chunks[index], similarity=float(similarities[index])) for index in top_indexes]

    def has_user_documents(self, user_id: int) -> bool:
        namespace = self._user_namespace(user_id)
        collection = self._collections.get(namespace)
        if collection is None and not self.load_index(namespace):
            return False
        return bool(self._collections[namespace].chunks)

    def faq_chunk_count(self) -> int:
        collection = self._collections.get("faq")
        if collection is None and not self.load_index("faq"):
            return 0
        return len(self._collections["faq"].chunks)

    def _create_index(self, embeddings: np.ndarray):
        if embeddings.size == 0:
            return None
        if faiss is None:
            return None
        index = faiss.IndexFlatIP(self.embedding_dimension)
        index.add(embeddings.astype(np.float32))
        return index

    def _materialize_results(self, collection: NamespaceCollection, scores: Any, indexes: Any) -> list[SearchResult]:
        results: list[SearchResult] = []
        for score, index in zip(scores, indexes):
            if index < 0:
                continue
            results.append(SearchResult(chunk=collection.chunks[int(index)], similarity=float(score)))
        return results

    @staticmethod
    def _user_namespace(user_id: int) -> str:
        return f"user_{user_id}"
