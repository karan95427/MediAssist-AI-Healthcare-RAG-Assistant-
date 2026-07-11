from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class QueryMode(str, Enum):
    FAQ = "faq"
    DOCUMENT = "document"


@dataclass(slots=True)
class QueryDecision:
    mode: QueryMode
    reason: str


class QueryRouter:
    def __init__(self) -> None:
        self._personal_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"\bmy\b",
                r"\bmine\b",
                r"\breport\b",
                r"\bprescribed\b",
                r"\bdischarge\b",
                r"\bfollow[- ]?up\b",
                r"\bmedications?\b",
                r"\blab\b",
                r"\bresult\b",
                r"\bcholesterol\b",
                r"\bhba1c\b",
                r"\bscan\b",
                r"\bdiagnosis\b",
            ]
        ]

    def route(self, question: str, has_uploaded_documents: bool) -> QueryDecision:
        if has_uploaded_documents and any(pattern.search(question) for pattern in self._personal_patterns):
            return QueryDecision(mode=QueryMode.DOCUMENT, reason="Question refers to a personal record or uploaded report.")
        return QueryDecision(
            mode=QueryMode.FAQ,
            reason="Question is general-purpose or no uploaded documents are available.",
        )
