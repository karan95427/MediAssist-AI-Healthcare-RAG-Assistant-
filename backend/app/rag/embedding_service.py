from __future__ import annotations

from hashlib import sha256
import logging

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    @property
    def dimension(self) -> int:
        self._ensure_model()
        return self._dimension

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        model = self._ensure_model()
        if model is None:
            return np.vstack([self._fallback_embedding(text) for text in texts]).astype(np.float32)

        embeddings = model.encode(texts, normalize_embeddings=True)
        return np.asarray(embeddings, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_texts([text])[0]

    def _ensure_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._dimension = int(self._model.get_sentence_embedding_dimension())
            logger.info("Loaded embedding model %s", self.model_name)
        except Exception as exc:
            logger.warning("Falling back to deterministic embeddings because sentence-transformers could not load: %s", exc)
            self._model = None
            self._dimension = 384
        return self._model

    def _fallback_embedding(self, text: str) -> np.ndarray:
        vector = np.zeros(self._dimension, dtype=np.float32)
        for token in text.lower().split():
            digest = sha256(token.encode("utf-8")).digest()
            for index, byte in enumerate(digest):
                vector[index % self._dimension] += byte / 255.0
        norm = np.linalg.norm(vector)
        return vector if norm == 0 else vector / norm
