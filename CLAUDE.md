# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All workflows go through the `Makefile` (run `make help` for the full list). The Makefile assumes a `.venv` created by `make setup`; commands invoke tools via `.venv/bin/...`.

```bash
make setup            # First-time: create venv, install deps (-e ".[dev]"), pre-commit, migrate, seed, npm install
make run              # Start backend (uvicorn :8000) + frontend (vite :5173) together
make test-unit        # Unit tests only, ~30s  (pytest tests/unit -m unit)
make test-integration # Integration tests (require Docker services up)
make test-all         # Full suite
make check            # lint + format + typecheck (run before committing)
make migrate          # alembic upgrade head
make seed             # Re-seed DB from scripts/seed_db.py
make reset-db         # Drop + recreate pathreview_dev, migrate, seed
make eval             # RAG evaluation suite (scripts/run_evals.py)
```

Backing services (Postgres :5433, Redis :6379, ChromaDB :8001) must be running before setup/tests: `docker compose up -d`.

**Running a single test / narrower scope** (pytest markers are `unit`, `integration`, `benchmark`, `security`):
```bash
.venv/bin/pytest tests/unit/test_pii_scrubber.py -v
.venv/bin/pytest tests/unit/test_pii_scrubber.py::test_name -v
.venv/bin/pytest tests/ -m security -v
```

**Individual quality tools** (what `make check` runs): `ruff check .`, `black .`, `mypy api/ core/ ingestion/ rag/ agent/ safety/`. mypy runs with `disallow_untyped_defs` — new functions in those packages need type annotations. Line length is 100 (ruff + black).

**Frontend** (from `frontend/`): `npm run dev`, `npm run build` (`tsc && vite build`), `npm test` (vitest), `npm run test:coverage`. Accessibility is tested via `jest-axe`.

## Architecture

PathReview analyzes GitHub profiles, resumes, and repos to generate portfolio feedback. The backend is async Python (FastAPI + SQLAlchemy 2.0 async + asyncpg). Request data flows through six subsystems in sequence — see `docs/ARCHITECTURE.md` for the full diagram and `docs/adr/` for design-decision records.

```
API (api/) → Ingestion (ingestion/) → Agent (agent/) → RAG (rag/) → Safety (safety/) → output
```

- **`api/`** — FastAPI app (`api/main.py`). `routes/` (auth, profiles, reviews, health) delegate to `core/services/`; `schemas/` are the Pydantic request/response models; `middleware/` handles JWT auth and request IDs. Routes are thin — business logic lives in services, not routes.
- **`core/`** — Shared foundation, imported everywhere. `config.py` is the single `settings` object (pydantic-settings, loaded from `.env`); `database.py` owns the async engine, `get_db` dependency, and `Base`; `models/` are SQLAlchemy ORM models; `services/` hold business logic; `security.py` handles JWT/password hashing.
- **`ingestion/`** — `pipeline.py` orchestrates parse → chunk → embed → store. Parsers subclass `parsers/base.py`; chunkers subclass `chunking/base.py` with a `strategy_selector`; embeddings go through the `EmbeddingProvider` ABC in `embeddings/provider.py`.
- **`agent/`** — Plan-execute orchestrator (`orchestrator.py`) that runs analysis tools. Every tool subclasses `agent/tools/base.py` (`name`, `description`, `execute()`): github_tool, skill_extractor, tech_detector, readme_scorer, market_analyzer. `memory/` holds session/context state; `error_handling.py` wraps tools with retry/timeout.
- **`rag/`** — `retriever/hybrid.py` combines `vector_store.py` (ChromaDB) + `keyword_search.py` (BM25); `generator/` builds prompts and calls the LLM; `evaluator/` scores relevance and faithfulness (used by `make eval`).
- **`safety/`** — Sequenced guardrails: prompt_defense → content_filter → bias_detector → pii_scrubber, plus `rate_limiter.py` and `monitoring.py`.

### Pluggable providers (key pattern)

Both the LLM and embeddings are provider-swappable, defaulting to deterministic **mock** implementations so the app and tests run with no API keys or network:
- `settings.llm_provider` defaults to `"mock"`. Real generation (`rag/generator/review_generator.py`) uses the OpenAI SDK pointed at a configurable `base_url` — set to OpenRouter by default (`openrouter_model`, `openrouter_base_url`). So "OpenAI" and "OpenRouter" both route through the same client.
- `embeddings/provider.py` has `MockEmbeddingProvider` (deterministic 1536-dim vectors from a text hash) as the default.

When adding a tool, parser, chunker, or provider, subclass the corresponding `base.py` ABC rather than wiring it in ad hoc.

### Database & migrations

Postgres via async SQLAlchemy. Schema changes require an Alembic migration in `alembic/versions/` (`make migrate` to apply). `init_db()` in `core/database.py` exists for convenience but migrations are the source of truth for schema.

## Conventions

- Config is centralized: import `from core.config import settings` — do not read `os.environ` directly.
- Logging is structured via `structlog` (`log = structlog.get_logger()`), not the stdlib `logging` module or `print`.
- The codebase is async throughout the request path (async SQLAlchemy, asyncpg) — use `async def` / `await` in services and routes.
- pre-commit runs ruff (--fix), black, and mypy on commit; `make check` mirrors this.
