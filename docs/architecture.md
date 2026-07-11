# Architecture Notes

MediAssist AI is intentionally scaffolded with strong boundaries:

- `api/` contains HTTP route definitions only.
- `services/` contains business logic and orchestration.
- `auth/` contains JWT, password hashing, and auth dependencies.
- `database/` contains engine, session, and declarative base setup.
- `models/` contains SQLAlchemy ORM models.
- `schemas/` contains request and response contracts.
- `frontend/src/services/` contains API-facing client code.

Future RAG components should be introduced behind service interfaces rather than directly inside API handlers.
