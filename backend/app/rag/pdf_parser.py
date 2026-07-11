from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str


class PDFParser:
    def parse(self, file_path: str | Path) -> list[ParsedPage]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            return self._parse_with_pymupdf(path)
        except Exception as exc:
            logger.warning("PyMuPDF parsing failed for %s: %s", path, exc)
            return self._parse_with_pypdf2(path)

    def _parse_with_pymupdf(self, path: Path) -> list[ParsedPage]:
        import fitz  # type: ignore

        pages: list[ParsedPage] = []
        with fitz.open(path) as document:
            for page_index in range(document.page_count):
                text = document.load_page(page_index).get_text("text").strip()
                if text:
                    pages.append(ParsedPage(page_number=page_index + 1, text=text))
        return pages

    def _parse_with_pypdf2(self, path: Path) -> list[ParsedPage]:
        from PyPDF2 import PdfReader

        pages: list[ParsedPage] = []
        reader = PdfReader(str(path))
        for page_index, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(ParsedPage(page_number=page_index + 1, text=text))
        return pages
