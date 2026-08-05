# AGENTS.md

Guide for AI coding agents working in the PathReview repository. Read this before making changes.

## Project Overview

PathReview is an AI-powered portfolio review assistant. It is a multi-service Python 3.11 backend (FastAPI) with a React + TypeScript (Vite) frontend. Subsystems live in top-level packages: `api/`, `core/`, `ingestion/`, `rag/`, `agent/`, `safety/`, plus `frontend/`. See `docs/ARCHITECTURE.md` for details.

| Subsystem | Directory | Responsibility |
|---|---|---|
| API Layer | `api/` | FastAPI app, routers, middleware, Pydantic schemas |
| Core | `core/` | Config (`core/config.py`), DB session, ORM models, security (JWT/bcrypt), services, structured logging |
| Ingestion | `ingestion/` | Parsers (resume/README/repo), chunking, embedding providers, `pipeline.py` |
| RAG | `rag/` | Retriever, LLM generator (`review_generator.py`), prompt templates, evaluator |
| Agent | `agent/` | `orchestrator.py` plan-execute loop, `tools/` (BaseTool + ToolResult), session memory, retry/error handling |
| Safety | `safety/` | PII scrubbing, bias detection, content filter, prompt defense, rate limiter |
| Frontend | `frontend/` | React 18 + TS dashboard (Vite/Vitest) |

Backing services (Postgres 16, Redis 7, ChromaDB) run via `docker compose up -d` and must be running before `make setup` or integration tests. The Python virtualenv lives at `.venv/` (`.venv/bin` on Unix, `.venv/Scripts` on Windows Git Bash). Activate it (`source .venv/bin/activate`) before running `python`/`pytest` directly.

## Build & Setup

```bash
cp .env.example .env            # then add keys; LLM_PROVIDER=mock needs no API key
docker compose up -d            # start Postgres, Redis, ChromaDB
make setup                      # venv + deps (pip install -e ".[dev]"), migrations, seed, frontend install
make run                        # backend (uvicorn api.main:app :8000) + frontend (vite :5173)
```

**Python 3.11 is required** (`requires-python = ">=3.11"`; `make setup` runs `python -m venv .venv`). If your system Python is newer (e.g. 3.13/3.14), `make setup` fails on later steps. Use an explicit 3.11 interpreter instead — e.g. `uv venv --python 3.11` then run the remaining `setup` steps (`pip install -e ".[dev]"`, `alembic upgrade head`, `python scripts/seed_db.py`, `cd frontend && npm ci`) manually. Activate with `source .venv/bin/activate` before `python`/`pytest`.

## Test Commands

Most Python tests use the `LLM_PROVIDER=mock` env (set it in CI; locally it comes from `.env`).

```bash
make test-unit                  # .venv/bin/pytest tests/unit -v -m unit
make test-integration           # needs docker compose services + DATABASE_URL/REDIS_URL
make test-all                   # .venv/bin/pytest tests/ -v
```

CI (`.github/workflows/ci.yml`) runs `ruff check .` + `black --check .`, `mypy ... --ignore-missing-imports`, `pytest tests/unit -v --tb=short`, `pytest tests/integration -v --tb=short` (all with `LLM_PROVIDER=mock`), and `cd frontend && npm test -- --run` on Node 18. A separate `.github/workflows/eval.yml` runs the RAG eval suite.

### Running a single test (Python)

```bash
# Single file
.venv/bin/pytest tests/unit/test_readme_scorer.py -v
# Single test function
.venv/bin/pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -v
# By name pattern
.venv/bin/pytest tests/unit -v -k "email_redaction"
# Drop -m unit to run regardless of marker; add -x to stop on first failure
```

### Frontend tests (Vitest)

```bash
cd frontend && npm test                              # watch mode
cd frontend && npm test -- --run                     # single run (CI uses this)
cd frontend && npm test -- --run src/components/__tests__/ReviewSection.test.tsx   # single file
```

## Lint / Format / Typecheck

Always run `make check` before considering work done. CI (`.github/workflows/ci.yml`) enforces these.

```bash
make lint       # .venv/bin/ruff check .      (CI: ruff check .)
make format     # .venv/bin/black .           (CI: black --check .)
make typecheck  # .venv/bin/mypy api/ core/ ingestion/ rag/ agent/ safety/
make check      # lint + format + typecheck
```

`pre-commit` runs `ruff --fix`, `black`, and `mypy --ignore-missing-imports` on staged files. If you skip the virtualenv, prefix with `python -m` (e.g. `python -m ruff check .`).

## Database

```bash
make migrate    # alembic upgrade head
make seed       # python scripts/seed_db.py
make reset-db   # drop + recreate pathreview_dev, migrate, seed
make eval       # python scripts/run_evals.py  (RAG eval suite, triggered on rag/ or ingestion/ changes)
```

## Key Files

- `core/config.py` — `settings` singleton (pydantic-settings, reads `.env`); all config/secrets come from here.
- `core/database.py` — `Base`, `get_db` async session dependency, `init_db`.
- `api/main.py` — FastAPI app factory, middleware, exception handler, router registration.
- `api/routes/` — `auth`, `profiles`, `reviews`, `health` routers.
- `ingestion/pipeline.py` — `IngestionPipeline` (resume/README/repo ingestion); parser registry.
- `agent/orchestrator.py` — `Orchestrator` plan-execute loop; tool registry.
- `rag/generator/review_generator.py` — LLM review generation (OpenAI/OpenRouter client).
- `tests/conftest.py` — shared fixtures (`sample_resume_text`, `sample_readme_text`).

## Code Style — Python

- **Python 3.11+, line length 100.** Formatted by `black`; linted by `ruff`.
- **Ruff rules:** `E, F, I, N, W, UP, B, SIM, TCH` (see `pyproject.toml`). `E501` is ignored in `core/models/`, `scripts/`, and `alembic/versions/`.
- **Imports:** ruff isort (`I`) ordering — stdlib, third-party, first-party. Use relative imports within a package (`from .base import BaseTool`), absolute imports across packages (`from core.config import settings`).
- **Types are mandatory.** `mypy` runs with `disallow_untyped_defs = true` and `warn_return_any = true`: every public function and method needs annotations and a return type. Prefer modern syntax: `str | None`, `list[dict]`, `dict[str, Any]` over `typing.Optional`/`typing.List` (legacy code mixes both; new code uses PEP 604).
- **Docstrings:** Google-style on all public functions and classes, with `Args:` / `Returns:` / `Raises:` sections (see `core/security.py`, `agent/tools/base.py`).
- **Logging:** use `structlog`, never `print`. Create one logger per module: `log = structlog.get_logger()` (or `logger = ...`). Emit structured key-value events: `log.info("review_created", review_id=str(review.id), user_id=...)`. Configure via `core/logging.py` (`configure_logging()`).
- **Async:** FastAPI endpoints are `async def`. Use `Annotated[AsyncSession, Depends(get_db)]` for DI. SQLAlchemy uses async (`sqlalchemy.ext.asyncio.AsyncSession`, `await db.execute(...)`, `await db.commit()`).
- **Error handling (routes):** wrap in try/except; re-raise `HTTPException`; catch `Exception`, `log.error(...)`, `await db.rollback()`, and `raise HTTPException(status_code=500, ...) from exc`. See `api/routes/auth.py`, `api/routes/reviews.py`.
- **Schemas:** Pydantic v2 (`api/schemas/`). ORM responses use `model_config = {"from_attributes": True}`.
- **Models:** SQLAlchemy 2.0 `Mapped[]` / `mapped_column()` style (see `core/models/`). UUIDs stored as strings; `datetime.utcnow` defaults; relationships via `relationship()` with `back_populates`.
- **Tools / parsers / providers:** extend the ABC base class (`BaseTool`, `BaseParser`, `EmbeddingProvider`) and return the project's dataclass result (`ToolResult`, `ParseResult`). Register new tools in `agent/orchestrator.py`, new parsers in `ingestion/pipeline.py`.
- **Tests:** pytest, markers `unit` / `integration` / `benchmark` / `security` (defined in `pyproject.toml`). Class-based suites (`class TestReadmeScorer:`), each with a fixture creating the instance under test. Shared fixtures live in `tests/conftest.py`. Use `MockEmbeddingProvider` / `LLM_PROVIDER=mock` — do not call real LLM APIs in unit tests. Pattern:

```python
@pytest.mark.unit
class TestPIIScrubber:
    @pytest.fixture
    def scrubber(self):
        return PIIScrubber()

    def test_email_redaction(self, scrubber):
        assert "[REDACTED]" in scrubber.scrub("Contact john@example.com")
```

## Code Style — Frontend

- **React 18 + TypeScript strict** (`tsconfig.json` `strict: true`), Vite, Vitest with jsdom + `@testing-library/react`.
- **Components:** function components typed `React.FC`; hooks in `src/hooks/`; shared types in `src/types/index.ts`; API calls via the `apiClient` singleton in `src/services/api.ts`.
- **Styling:** Tailwind utility classes inline. Icons from `lucide-react`.
- **Tests:** colocated under `src/**/__tests__/*.test.tsx`. Use `describe`/`it` from `vitest`; globals are enabled. Setup file: `src/test/setup.ts`. Run a single file with `npm test -- --run <path>`.
- **Build:** `cd frontend && npm run build` (runs `tsc && vite build`).
- **Install deps with `npm ci` — never `npm install` / `npm install .`** — `npm install` re-resolves the `^` ranges in `package.json` and rewrites `package-lock.json` (adding `peer`/`os`/`cpu` annotations and bumping versions). `npm ci` installs the exact versions pinned in the lockfile (failing if out of sync) and matches CI. Only run `npm install` if you intentionally want to update dependency versions, and commit the regenerated lock deliberately.

## Git Conventions

- **Commits:** Conventional Commits — `<type>(<scope>): <description>`. Scopes: `ingestion`, `rag`, `agent`, `safety`, `api`, `frontend`. Types: `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`, `ci`. Reference issues in the footer (`Fixes #42`).
- **Branches:** `<type>/<issue-number>-<short-description>` (e.g. `fix/124-resume-parser-index-error`).
- **Never commit secrets** (`.env` is gitignored). Do not hardcode API keys; read from `core.config.settings`.
- **PRs:** fill out `.github/PULL_REQUEST_TEMPLATE.md` and confirm `make check && make test-unit` pass.

## Adding a New Tool / Parser

1. Create a new file in `agent/tools/` (or `ingestion/parsers/`); extend the ABC base class (`BaseTool` / `BaseParser`).
2. Return the project's dataclass result (`ToolResult` / `ParseResult`); add `name` and `description` class attrs on tools.
3. Register it in `agent/orchestrator.py` (tools) or `ingestion/pipeline.py` (parsers).
4. Add unit tests in `tests/unit/test_<name>.py` (class-based, `@pytest.mark.unit`, fixture for the instance).
5. Add mock fixtures in `tests/fixtures/` if the tool/parser calls external APIs.

## Agent Workflow Checklist

1. Reproduce/understand via tests and `docs/`. Add or update tests alongside any code change.
2. Use `LLM_PROVIDER=mock` for local/test work — never require a real API key.
3. Run `make check` (lint + format + typecheck) and the relevant test command.
4. Prefer editing existing files and patterns over creating new ones. Mimic the nearest neighbor's style.
5. Do not commit unless explicitly asked. Do not add comments unless requested.
