from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"


class Settings(BaseSettings):
    project_name: str = "MediAssist AI"
    api_v1_str: str = "/api/v1"
    secret_key: str = Field("change-this-in-production", min_length=16)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./mediassist.db"
    backend_cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    gemini_api_key: str = "placeholder"
    gemini_model: str = "gemini-3.5-flash"
    faiss_index_path: str = str(BACKEND_DIR / "app" / "data" / "vector_store")
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_upload_size_mb: int = 20
    upload_dir: str = str(BACKEND_DIR / "app" / "uploads")
    knowledge_base_dir: str = str(BACKEND_DIR / "app" / "knowledge_base")
    dataset_dir: str = str(BACKEND_DIR / "backend" / "app" / "data" / "dataset")
    local_base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    fine_tuned_model_dir: str = str(BACKEND_DIR / "app" / "data" / "qwen2_5_1_5b_lora")
    retrieval_top_k: int = 5
    chunk_size_words: int = 500
    chunk_overlap_words: int = 100

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("faiss_index_path", "upload_dir", "knowledge_base_dir", "dataset_dir", "fine_tuned_model_dir", mode="before")
    @classmethod
    def resolve_project_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute():
            return str(path)
        normalized = value.replace("./", "", 1).replace(".\\", "", 1)
        return str((ROOT_DIR / normalized).resolve())

    @field_validator("gemini_model", mode="before")
    @classmethod
    def normalize_gemini_model(cls, value: str) -> str:
        return value.replace("models/", "", 1).strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
