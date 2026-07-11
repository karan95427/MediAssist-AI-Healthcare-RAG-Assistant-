from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config.settings import ROOT_DIR, get_settings

settings = get_settings()
LEGACY_DATASET_DIR = ROOT_DIR / "backend" / "backend" / "app" / "data" / "dataset"


@dataclass(slots=True)
class TrainingExample:
    prompt: str
    response: str
    source: str


class FineTuningDatasetBuilder:
    def __init__(self, dataset_dir: str | None = None) -> None:
        candidate = Path(dataset_dir or settings.dataset_dir)
        self.dataset_dir = candidate if candidate.exists() else LEGACY_DATASET_DIR

    def build_examples(self) -> list[TrainingExample]:
        examples: list[TrainingExample] = []
        examples.extend(self._load_medquad_examples())
        examples.extend(self._load_healthcare_magic_examples())
        examples.extend(self._load_chatbot_examples())
        examples.extend(self._load_symptom_examples())
        return self._deduplicate([example for example in examples if example.prompt and example.response])

    def _load_medquad_examples(self) -> list[TrainingExample]:
        path = self.dataset_dir / "medquad1.csv"
        if not path.exists():
            return []

        examples: list[TrainingExample] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                question = self._clean_text(row.get("question"))
                answer = self._clean_text(row.get("answer"))
                focus_area = self._clean_text(row.get("focus_area"))
                source = self._clean_text(row.get("source"))
                if not question or not answer:
                    continue
                prompt = (
                    "Answer this healthcare FAQ clearly and safely for a patient. "
                    "Do not diagnose, prescribe, or invent facts.\n"
                    f"Topic: {focus_area or 'General healthcare'}\n"
                    f"Question: {question}"
                )
                response = answer
                if source:
                    response = f"{response}\n\nReference source: {source}"
                examples.append(TrainingExample(prompt=prompt, response=response, source=path.name))
        return examples

    def _load_healthcare_magic_examples(self) -> list[TrainingExample]:
        path = self.dataset_dir / "HealthCareMagic-100k.json"
        if not path.exists():
            return []

        examples: list[TrainingExample] = []
        for item in self._iter_json_items(path):
            instruction = self._clean_text(item.get("instruction"))
            patient_input = self._clean_text(item.get("input"))
            output = self._clean_text(item.get("output"))
            if not patient_input or not output:
                continue
            prompt = (
                "Respond as MediAssist AI, a safe healthcare assistant. "
                "Explain in patient-friendly language, include practical next steps, "
                "and advise consulting a qualified healthcare professional when appropriate.\n"
                f"Instruction: {instruction or 'Answer the patient healthcare question.'}\n"
                f"Patient message: {patient_input}"
            )
            examples.append(TrainingExample(prompt=prompt, response=output, source=path.name))
        return examples

    def _load_chatbot_examples(self) -> list[TrainingExample]:
        path = self.dataset_dir / "ai-medical-chatbot.csv"
        if not path.exists():
            return []

        examples: list[TrainingExample] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                description = self._clean_text(row.get("Description"))
                patient = self._clean_text(row.get("Patient"))
                doctor = self._clean_text(row.get("Doctor"))
                prompt = (
                    "Respond as MediAssist AI, a safe healthcare assistant. "
                    "Use patient-friendly language and avoid unsupported diagnosis.\n"
                    f"Healthcare question: {description}\n"
                    f"Patient message: {patient}"
                ).strip()
                response = doctor
                if prompt and response:
                    examples.append(TrainingExample(prompt=prompt, response=response, source=path.name))
        return examples

    def _load_symptom_examples(self) -> list[TrainingExample]:
        path = self.dataset_dir / "Healthcare.csv"
        if not path.exists():
            return []

        examples: list[TrainingExample] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                symptoms = self._clean_text(row.get("Symptoms"))
                disease = self._clean_text(row.get("Disease"))
                age = self._clean_text(row.get("Age"))
                gender = self._clean_text(row.get("Gender"))
                if not symptoms or not disease:
                    continue
                prompt = (
                    "Summarize possible educational condition information from this symptom dataset. "
                    "State clearly that this is not a diagnosis and the user should consult a clinician.\n"
                    f"Age: {age}\nGender: {gender}\nSymptoms: {symptoms}"
                )
                response = (
                    f"The dataset label associated with these symptoms is {disease}. "
                    "This is educational information only, not a diagnosis. A qualified healthcare "
                    "professional should evaluate symptoms, history, and tests before making clinical decisions."
                )
                examples.append(TrainingExample(prompt=prompt, response=response, source=path.name))
        return examples

    def _iter_json_items(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            first_char = handle.read(1)
            handle.seek(0)
            if first_char == "[":
                data = json.load(handle)
                return [item for item in data if isinstance(item, dict)]

            items: list[dict[str, Any]] = []
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    items.append(item)
            return items

    def _deduplicate(self, examples: list[TrainingExample]) -> list[TrainingExample]:
        unique_examples: list[TrainingExample] = []
        seen: set[tuple[str, str]] = set()
        for example in examples:
            key = (example.prompt.lower(), example.response.lower())
            if key in seen:
                continue
            seen.add(key)
            unique_examples.append(example)
        return unique_examples

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""
        return " ".join(str(value).replace("\x00", " ").split()).strip()
