from __future__ import annotations

import json
import logging
import re
from textwrap import dedent
from urllib import error, request

from app.config.settings import get_settings
from app.rag.local_model_service import LocalModelService
from app.rag.retriever import RetrievedChunk

logger = logging.getLogger(__name__)
settings = get_settings()
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
MODEL_NOT_READY_MESSAGE = (
    "The local healthcare chatbot model is not trained yet. Train the model first, then restart the backend."
)


class LLMService:
    def __init__(self) -> None:
        self.local_model_service = LocalModelService()

    def answer_question(self, question: str, contexts: list[RetrievedChunk] | None = None) -> str:
        draft = self.local_model_service.answer_question(question, contexts or [])
        if not draft:
            return self._safe_fallback_answer(question) or MODEL_NOT_READY_MESSAGE

        if self._needs_quality_fallback(draft):
            fallback = self._safe_fallback_answer(question)
            if fallback:
                return fallback

        polished = self._polish_with_gemini(question, draft)
        return polished or draft

    def _polish_with_gemini(self, question: str, draft: str) -> str | None:
        if not settings.gemini_api_key or settings.gemini_api_key == "placeholder":
            return None

        prompt = self._build_polish_prompt(question, draft)
        models_to_try = [settings.gemini_model, *[model for model in FALLBACK_MODELS if model != settings.gemini_model]]
        for model_name in models_to_try:
            try:
                return self._call_gemini(prompt, model_name, max_output_tokens=1200)
            except Exception as exc:
                logger.warning("Gemini polish failed for model %s: %s", model_name, exc)
                continue
        return None

    def _build_polish_prompt(self, question: str, draft: str) -> str:
        return dedent(
            f"""
            You are a response editor for MediAssist AI.

            Polish the draft answer only. Do not add new medical facts, values, claims, diagnoses, medications, or treatment steps that are not already present in the draft. Do not mention sources, documents, retrieval, pages, similarity, or citations.

            Make the response professional, complete, concise, and patient-friendly. If the draft is unsafe or unclear, make it safer while preserving its meaning. End with a complete sentence.

            User question:
            {question}

            Draft answer from local model:
            {draft}
            """
        ).strip()

    def _call_gemini(self, prompt: str, model_name: str, max_output_tokens: int) -> str:
        normalized_model = model_name.replace("models/", "", 1)
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{normalized_model}:generateContent"
            f"?key={settings.gemini_api_key}"
        )
        payload = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.15, "topP": 0.8, "maxOutputTokens": max_output_tokens},
            }
        ).encode("utf-8")
        http_request = request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(http_request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
        candidates = body.get("candidates", [])
        if not candidates:
            raise error.HTTPError(endpoint, 502, "No Gemini candidates returned", hdrs=None, fp=None)
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise ValueError("Gemini returned an empty polish response")
        return text

    @staticmethod
    def _needs_quality_fallback(answer: str) -> bool:
        text = answer.strip()
        lower = text.lower()
        if not text:
            return True
        if len(text) > 2600:
            return True
        if text[-1] not in ".!?":
            return True
        if lower.count("learn more") >= 2:
            return True
        if lower.count("nih") >= 3:
            return True
        if re.search(r"(?:^|\n)\s*(?:[-*]|\d+[.)])\s*\S{0,35}$", text):
            return True
        return False

    def _safe_fallback_answer(self, question: str) -> str | None:
        normalized = question.lower()
        if "cancer" in normalized and any(word in normalized for word in ("treatment", "treat", "therapy", "options")):
            condition = self._extract_condition(question) or "cancer"
            return self._cancer_treatment_answer(condition)
        return None

    @staticmethod
    def _extract_condition(question: str) -> str | None:
        match = re.search(r"(?:for|of|about)\s+([a-zA-Z\s-]*cancer)", question, flags=re.IGNORECASE)
        if not match:
            return None
        condition = re.sub(r"\s+", " ", match.group(1)).strip().lower()
        return condition

    @staticmethod
    def _cancer_treatment_answer(condition: str) -> str:
        label = condition.title()
        return (
            f"Treatment for {label} depends on the cancer type, stage, tumor location, test results, symptoms, and the person's overall health. "
            "Doctors often use more than one treatment, so the final plan is usually individualized by an oncology team.\n\n"
            "Common treatment options include:\n\n"
            "- Surgery: This may be used when the cancer is localized and can be removed safely. It is more common in earlier-stage disease.\n"
            "- Radiation therapy: High-energy radiation can target cancer cells in a specific area. It may be used alone or with other treatments.\n"
            "- Chemotherapy: These medicines travel through the body to kill or slow fast-growing cancer cells. Chemotherapy may be used before or after surgery, or for advanced disease.\n"
            "- Targeted therapy: These medicines work against specific changes in cancer cells. They are usually chosen after molecular or genetic testing of the tumor.\n"
            "- Immunotherapy: This helps the immune system recognize and attack cancer cells. It is used for some cancers depending on stage and biomarker results.\n"
            "- Supportive and palliative care: This focuses on symptoms, breathing, pain, nutrition, fatigue, and quality of life. It can be used at any stage along with cancer-directed treatment.\n\n"
            "The best next step is to discuss the exact stage, biopsy report, imaging results, and biomarker test results with an oncologist, because those details strongly affect the safest treatment choice."
        )
