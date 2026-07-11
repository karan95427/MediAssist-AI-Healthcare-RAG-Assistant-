# MediAssist AI

MediAssist AI is a production-oriented MVP scaffold for a healthcare-focused RAG assistant. This repository establishes the architecture, authentication, database foundation, frontend dashboard shell, and deployment setup required to evolve into a secure document-assisted clinical support product.

The RAG pipeline, embeddings, vector indexing, PDF processing, and Gemini integrations are intentionally left as placeholders.

## Project Overview

This codebase is split into a FastAPI backend and a React + Vite frontend. The backend provides modular API routing, JWT authentication, SQLAlchemy persistence, configuration management, and service-layer separation. The frontend provides a professional medical dashboard shell with authentication pages, protected routes, and placeholder workflows for chat and document upload.

## Architecture Diagram

```text
+---------------------------+         +----------------------------------+
| React Frontend            |         | FastAPI Backend                  |
| - Auth Pages              |  HTTP   | - API Routers                    |
| - Dashboard Layout        +-------->+ - Auth Service                   |
| - Chat / Upload UI        |         | - User Service                   |
| - Axios Client            |         | - JWT / Password Hashing         |
+-------------+-------------+         | - SQLAlchemy ORM                 |
              |                       | - Config / Middleware / Schemas  |
              |                       +----------------+-----------------+
              |                                        |
              |                                        |
              v                                        v
      +-------------------+                 +---------------------------+
      | Future AI Layer   |                 | SQLite Database           |
      | - Gemini          |                 | Alembic-ready persistence |
      | - Embeddings      |                 | Easy PostgreSQL migration |
      | - FAISS           |                 +---------------------------+
      +-------------------+
```

## Folder Structure

```text
MediAssist-AI/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── config/
│   │   ├── database/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── services/
│   ├── Dockerfile
│   ├── package.json
│   └── tailwind.config.js
├── docs/
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

## Tech Stack

### Frontend
- React 18
- Vite
- TypeScript
- Tailwind CSS
- React Router
- Axios
- React Markdown

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- SQLite
- Pydantic Settings
- Passlib
- Python-Jose JWT
- Uvicorn

### AI Placeholders
- Gemini API
- Sentence Transformers
- FAISS

### DevOps
- Docker
- Docker Compose
- Environment variable driven configuration

## Installation

### 1. Configure environment

Copy `.env.example` to `.env` and adjust values as needed.

### 2. Run with Docker Compose

```bash
docker compose up --build
```

Frontend:
- `http://localhost:5173`

Backend:
- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 3. Run locally without Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Code Quality

- Clear separation between API, services, auth, schemas, and database layers
- Typed backend and frontend code
- Dependency injection used for database sessions and authenticated users
- Security-oriented auth scaffolding with JWT and password hashing
- Alembic-ready ORM metadata and migration configuration
- Placeholder AI service boundaries to prevent business logic leaking into routes

## Future Roadmap

- Document ingestion and PDF parsing
- Embeddings generation with Sentence Transformers
- FAISS vector indexing and retrieval
- Gemini-powered clinical Q&A orchestration
- Role-based access control
- Audit logging and observability
- PostgreSQL migration for production workloads
- Background jobs for ingestion pipelines
- Test suite, CI/CD, and security hardening
