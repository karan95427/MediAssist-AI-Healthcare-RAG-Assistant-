from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from app.rag.pdf_parser import ParsedPage


@dataclass(slots=True)
class KnowledgeDocument:
    document_name: str
    source_type: str
    pages: list[ParsedPage]


class KnowledgeLoader:
    def __init__(self, knowledge_base_dir: str, dataset_dir: str) -> None:
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.dataset_dir = Path(dataset_dir)

    def load(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        documents.extend(self._load_curated_documents())
        documents.extend(self._load_dataset_documents())
        return documents

    def _load_curated_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for file_path in self.knowledge_base_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() == ".pdf":
                continue
            text = file_path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            documents.append(
                KnowledgeDocument(
                    document_name=file_path.name,
                    source_type=file_path.parent.name,
                    pages=[ParsedPage(page_number=1, text=text)],
                )
            )
        return documents

    def _load_dataset_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        if not self.dataset_dir.exists():
            return documents

        chatbot_csv = self.dataset_dir / "ai-medical-chatbot.csv"
        if chatbot_csv.exists():
            documents.append(self._load_chatbot_dataset(chatbot_csv))

        healthcare_csv = self.dataset_dir / "Healthcare.csv"
        if healthcare_csv.exists():
            documents.append(self._load_symptom_dataset(healthcare_csv))

        return documents

    def _load_chatbot_dataset(self, path: Path) -> KnowledgeDocument:
        sections: list[str] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=1):
                description = (row.get("Description") or "").strip()
                patient = (row.get("Patient") or "").strip()
                doctor = (row.get("Doctor") or "").strip()
                if not any([description, patient, doctor]):
                    continue
                sections.append(
                    f"Record {index}\nQuestion: {description}\nPatient: {patient}\nDoctor guidance: {doctor}"
                )
        return KnowledgeDocument(
            document_name=path.name,
            source_type="dataset_chatbot",
            pages=[ParsedPage(page_number=1, text="\n\n".join(sections))],
        )

    def _load_symptom_dataset(self, path: Path) -> KnowledgeDocument:
        sections: list[str] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=1):
                symptoms = (row.get("Symptoms") or "").strip()
                disease = (row.get("Disease") or "").strip()
                age = (row.get("Age") or "").strip()
                gender = (row.get("Gender") or "").strip()
                if not symptoms or not disease:
                    continue
                sections.append(
                    f"Record {index}\nSymptoms: {symptoms}\nAssociated condition label: {disease}\nAge: {age}\nGender: {gender}"
                )
        return KnowledgeDocument(
            document_name=path.name,
            source_type="dataset_symptoms",
            pages=[ParsedPage(page_number=1, text="\n\n".join(sections))],
        )
