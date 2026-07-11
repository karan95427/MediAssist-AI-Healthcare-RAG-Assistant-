from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.session import create_db_and_tables
from app.middleware.correlation import CorrelationIdMiddleware
from app.services.chat_service import schedule_knowledge_base_refresh

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.2.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    schedule_knowledge_base_refresh()


app.include_router(api_router, prefix=settings.api_v1_str)
