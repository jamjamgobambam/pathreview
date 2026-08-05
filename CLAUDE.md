# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PathReview is an AI-powered portfolio review assistant for early-career developers. It ingests GitHub profiles, resumes, and repos, then uses a RAG pipeline and a multi-tool agent to generate structured, evidence-based portfolio feedback, guarded by a safety layer.

Stack: FastAPI + SQLAlchemy/Postgres backend (Python 3.11), React + TypeScript + Vite frontend, Redis, ChromaDB for vector storage, Alembic for migrations.

## Commands

Backend commands run through `.venv` (created by `make setup`); prefix manual invocations with `.venv/bin/` if not activated.

```bash
make setup           # first-time setup: venv, deps, migrations, seed data, frontend install
make run              # start backend (uvicorn, :8000) + frontend (vite, :5173) concurrently
make test-unit        # pytest tests/unit -v -m unit (~30s, no external deps)
make test-integration # pytest tests/integration -v -m integration (requires Docker services)
make test-all         # full pytest suite
make lint             # ruff check .
make format           # black .
make typecheck        # mypy api/ core/ ingestion/ rag/ agent/ safety/
make check            # lint + format + typecheck
make migrate          # alembic upgrade head
make seed             # re-seed database
make reset-db         # drop, recreate, migrate, and reseed the dev database
make eval             # run the RAG evaluation suite (scripts/run_evals.py)
```

Single test file/case: `.venv/bin/pytest tests/unit/test_relevance_scorer.py -v` or `-k test_name`.

Frontend (from `frontend/`): `npm run dev`, `npm test` (vitest), `npm run build` (tsc + vite build).

Docker services (Postgres + Redis) must be running (`docker compose up -d`) before `make setup` or `make test-integration`.

## Architecture

Five subsystems, roughly following this data flow: **API → Ingestion → Agent → RAG → Safety → Review Output**.

- **`api/`** — FastAPI app. Routes (`api/routes/`) handle JWT auth, validation, rate limiting, and delegate business logic to `core/services/`. Don't put business logic directly in route handlers.
- **`core/`** — Shared foundation: SQLAlchemy models (`core/models/`), service layer (`core/services/`), config, database session, security, logging. This is the dependency root other subsystems build on.
- **`ingestion/`** — Turns uploaded resumes/READMEs/repos into embeddings. Flow: `parsers/` (implement `BaseParser`, return `ParseResult`) → `chunking/` (`semantic_chunker.py` vs `structural_chunker.py`, selected via `strategy_selector.py`) → `embeddings/` (batched provider calls) → stored via `pipeline.py`, which orchestrates the whole parse→chunk→embed→store sequence and is where new parsers get registered.
- **`agent/`** — Plan-execute orchestrator (`orchestrator.py`) coordinating analysis tools in `agent/tools/` (github_tool, skill_extractor, readme_scorer, market_analyzer, tech_detector), each implementing `BaseTool` (`name`, `description`, `execute()`). Tools are registered in the orchestrator, which handles retries/timeouts and synthesizes results. `agent/memory/` manages session state and context across the agent run.
- **`rag/`** — `retriever/hybrid.py` combines vector similarity (`vector_store.py`, ChromaDB) with BM25 keyword search (`keyword_search.py`). `generator/` builds prompts (`prompt_templates.py`), calls the LLM (`review_generator.py`), and parses structured output (`output_parser.py`). `evaluator/` scores retrieval relevance (`relevance_scorer.py`) and generation faithfulness (`faithfulness_checker.py`) — this is what `make eval` exercises.
- **`safety/`** — Sequential middleware wrapping generation: prompt injection defense → content filter → bias detector → PII scrubber, plus rate limiting and monitoring. All safety events are logged with structured metadata.
- **`frontend/`** — React + TypeScript dashboard (Vite, react-router). Tests in `frontend/src/test/` via vitest + testing-library + jest-axe (accessibility).

See `docs/ARCHITECTURE.md` for the full diagram and `docs/adr/` for rationale on chunking strategy, embedding model choice, and agent orchestration design.

## Adding to the codebase

**New ingestion parser**: implement `BaseParser` in `ingestion/parsers/`, register in `ingestion/pipeline.py`, add tests in `tests/unit/test_<parser_name>.py`.

**New agent tool**: implement `BaseTool` in `agent/tools/`, register in `agent/orchestrator.py`, add tests in `tests/unit/test_<tool_name>.py` (mock external API calls).

## Conventions

- **Branch naming**: `<type>/<issue-number>-<short-description>` (e.g. `fix/124-resume-parser-index-error`). Types: `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`.
- **Commits**: Conventional Commits — `<type>(<scope>): <description>`. Scopes: `ingestion`, `rag`, `agent`, `safety`, `api`, `frontend`.
- **Python style**: black-formatted, ruff-linted (rules: E, F, I, N, W, UP, B, SIM, TCH), line length 100. mypy runs with `disallow_untyped_defs` and `check_untyped_defs` — new functions need full type annotations.
- **Docstrings**: Google-style, required on public functions/classes.
- Before opening a PR: `make check && make test-unit` must pass.

## Test markers

pytest markers (`pyproject.toml`): `unit` (fast, no external deps), `integration` (requires Docker services), `benchmark` (performance), `security` (red-team tests). Test suite lives under `tests/unit/`, `tests/integration/`, `tests/security/`, `tests/benchmarks/`.
