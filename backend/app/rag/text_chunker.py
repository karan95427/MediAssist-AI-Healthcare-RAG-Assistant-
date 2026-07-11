from __future__ import annotations

from dataclasses import dataclass

from app.rag.pdf_parser import ParsedPage


@dataclass(slots=True)
class TextChunk:
    chunk_id: str
    document_name: str
    page_number: int
    text: str
    source_type: str
    user_id: int | None = None
    document_id: int | None = None


class TextChunker:
    def __init__(self, chunk_size_words: int = 500, overlap_words: int = 100) -> None:
        if overlap_words >= chunk_size_words:
            raise ValueError("overlap_words must be smaller than chunk_size_words")
        self.chunk_size_words = chunk_size_words
        self.overlap_words = overlap_words

    def chunk_pages(
        self,
        pages: list[ParsedPage],
        document_name: str,
        source_type: str,
        user_id: int | None = None,
        document_id: int | None = None,
    ) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        for page in pages:
            words = page.text.split()
            if not words:
                continue

            step = self.chunk_size_words - self.overlap_words
            for start in range(0, len(words), step):
                chunk_words = words[start : start + self.chunk_size_words]
                if not chunk_words:
                    continue
                chunk_index = len(chunks) + 1
                chunks.append(
                    TextChunk(
                        chunk_id=f"{document_name}-{page.page_number}-{chunk_index}",
                        document_name=document_name,
                        page_number=page.page_number,
                        text=" ".join(chunk_words),
                        source_type=source_type,
                        user_id=user_id,
                        document_id=document_id,
                    )
                )
                if start + self.chunk_size_words >= len(words):
                    break
        return chunks
