# Development Journal

## Environment setup — 2026-07-20

Bootstrapped a local development environment for PathReview.

**Verified working:**
- Backing services (`docker compose up -d`): `db`, `redis`, `vector-db` all healthy
- Python venv on 3.13.11 (`make setup`), deps installed via `pip install -e ".[dev]"`
- Alembic migrations applied (head `002`), database seeded
- Frontend deps installed; `make run` serves backend on :8000 and frontend on :5173

**Setup fixes required on this machine:**
- `Makefile` — venv bootstrap now auto-detects Python ≥3.11 (`python3.13/3.12/3.11`)
  instead of the hardcoded system `python`/`python3` (which was 3.9, violating
  `requires-python >= 3.11`).
- `docker-compose.yml` — bumped `chromadb/chroma` from `0.4.22` to `0.5.23`; the
  `0.4.22` image crashes on startup under NumPy 2.0 (`np.float_` was removed).

**Notes / follow-ups:**
- `GET /health` returns 503 due to two pre-existing bugs in `api/routes/health.py`
  (raw `SELECT 1` needs `text()` for SQLAlchemy 2.0; redis check reads a nonexistent
  `settings.redis_host`/`redis_port`). Containers themselves are reachable.

## Next: issue #111 — property-based tests for the PII scrubber

Add `hypothesis`-based property tests in `tests/unit/test_pii_scrubber.py` that
generate randomized PII and assert the scrubber always removes it.
