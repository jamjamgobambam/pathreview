# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PathReview is an AI-powered portfolio review assistant: it ingests a user's resume, GitHub profile, and project repos, and produces structured, evidence-based feedback via a RAG pipeline and multi-tool agent.

Backend: Python 3.11 (FastAPI + async SQLAlchemy + Alembic + PostgreSQL + Redis + ChromaDB). Frontend: React + TypeScript + Vite, in `frontend/`.

## Commands

Backend commands run through the Makefile, which resolves the venv (`.venv/bin` on macOS/Linux, `.venv/Scripts` on Windows) — don't call `pytest`/`ruff`/`mypy` directly unless the venv is already activated.

```bash
make setup            # venv, deps, migrations, seed data, frontend install (first time only)
make run              # backend (uvicorn, :8000) + frontend (vite, :5173) concurrently

make test-unit         # tests/unit, marker `unit` (~30s, no external deps)
make test-integration  # tests/integration, marker `integration` (requires docker compose services)
make test-all          # full suite

make lint              # ruff check .
make format            # black .
make typecheck         # mypy api/ core/ ingestion/ rag/ agent/ safety/  (frontend is NOT included)
make check             # lint + format + typecheck

make migrate           # alembic upgrade head
make seed              # scripts/seed_db.py
make reset-db          # drop + recreate pathreview_dev, migrate, reseed
make eval              # scripts/run_evals.py — RAG evaluation suite
```

Run a single test: `.venv/bin/pytest tests/unit/test_readme_scorer.py::test_name -v`.

Docker-backed services (Postgres, Redis, ChromaDB) must be up before `make setup`/`make migrate`/integration tests: `docker compose up -d`. Postgres is exposed on host port **5433** (mapped to container 5432) to avoid clashing with any native Postgres install — `DATABASE_URL` must use `postgresql+asyncpg://...@localhost:5433/pathreview_dev`.

Frontend (from `frontend/`): `npm run dev`, `npm run build` (runs `tsc` then vite build), `npm run test` (vitest), `npm run test:coverage`.

Seeded test accounts (via `make setup`/`make seed`): `user1@example.com` / `password1`, `user2@example.com` / `password2`, `user3@example.com` / `password3`.

## Architecture

Request flow: **API layer → Ingestion pipeline → Agent orchestrator → RAG system → Safety layer → review output.**

- **`api/`** — FastAPI app (`api/main.py`). Routes in `api/routes/` delegate to the service layer in `core/services/` rather than containing business logic themselves. JWT auth and rate limiting live in `api/middleware/`.
- **`core/`** — Shared foundation: SQLAlchemy models (`core/models/`), async DB session/engine (`core/database.py`, async engine + `get_db()` FastAPI dependency), settings (`core/config.py`, a pydantic-settings singleton reading `.env`), and the service layer (`core/services/`) that routes call into.
- **`ingestion/`** — Turns uploaded documents into embeddings: parsers (`ingestion/parsers/`, implement `BaseParser.parse() -> ParseResult`) → chunkers (`ingestion/chunking/`, strategy selected per source type) → embeddings (`ingestion/embeddings/`) → vector store. Orchestrated by `ingestion/pipeline.py`. New parsers must be registered there (see "Adding a New Parser" below).
- **`agent/`** — Plan-execute orchestrator (`agent/orchestrator.py`) that runs analysis tools with retry/timeout policies and synthesizes results. Tools live in `agent/tools/` and implement `BaseTool` (`name`, `description`, `execute(input_data) -> ToolResult`). New tools must be registered in `agent/orchestrator.py`. Session/context state is in `agent/memory/`.
- **`rag/`** — Hybrid retrieval (`rag/retriever/`: vector similarity + BM25 keyword search combined) feeds `rag/generator/` (prompt templates + LLM call) to produce structured feedback; `rag/evaluator/` scores retrieval relevance and generation faithfulness (used by `make eval`).
- **`safety/`** — Sequential pipeline wrapping generation: prompt injection defense → content filter → bias detector → PII scrubber, with rate limiting and monitoring alongside. All safety events are logged with structured metadata.
- **`frontend/`** — React/TS dashboard (Vite). Talks to the API layer; no server-side rendering.

See `docs/ARCHITECTURE.md` for the full data-flow diagram and `docs/adr/` for the reasoning behind chunking strategy, embedding model choice, and agent orchestration approach.

## Conventions

- **Branch naming:** `<type>/<issue-number>-<short-description>` off `main`, e.g. `fix/124-resume-parser-index-error`. Types: `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`.
- **Commits:** Conventional Commits — `<type>(<scope>): <description>`. Scopes match subsystem directories: `ingestion`, `rag`, `agent`, `safety`, `api`, `frontend`.
- **Adding a parser:** create `ingestion/parsers/<name>.py` implementing `BaseParser`, register it in `ingestion/pipeline.py`, add tests in `tests/unit/test_<name>.py` (+ fixtures in `tests/fixtures/` if needed).
- **Adding an agent tool:** create `agent/tools/<name>.py` implementing `BaseTool`, register it in `agent/orchestrator.py`, add tests in `tests/unit/test_<name>.py` (+ mock responses in `tests/fixtures/` for tools calling external APIs).
- Ruff config ignores line-length (E501) in `core/models/`, `scripts/`, and `alembic/versions/`; mypy excludes `alembic/versions/` and otherwise requires typed defs everywhere under `api/ core/ ingestion/ rag/ agent/ safety/`.
- Pytest markers: `unit`, `integration`, `benchmark`, `security` — mark new tests accordingly so they run in the right `make test-*` target.
