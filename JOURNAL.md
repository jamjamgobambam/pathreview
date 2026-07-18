# Contribution Journal — PathReview

## 2026-07-17 — Environment setup

Got a local dev environment running end to end:

- Started Docker backing services (`docker compose up -d`): Postgres (`:5433`),
  Redis (`:6379`), ChromaDB (`:8001`).
- Created `.env` from `.env.example` (`LLM_PROVIDER=mock`, so no API key needed
  to run locally).
- Ran `make setup` (venv + deps + `alembic upgrade head` + seed + `npm install`).
- Ran `make run` and confirmed the frontend loads at **http://localhost:5173**
  (HTTP 200, "PathReview" React app) and the API serves docs at
  http://localhost:8000/docs.

Note: `/health` returns 503 due to two pre-existing app-code bugs (Postgres
health check needs `text("SELECT 1")`; Redis check references a missing
`redis_host` setting). Infra containers are healthy — these are separate from
the issue I'm working on.

## Issue chosen: #150 — Tech detector counts vendored/build files

`tier-1` / `good first issue`.

**Summary:** `agent/tools/tech_detector.py` mis-identifies a repo's primary
language because `_should_skip_file()` fails to exclude top-level `node_modules/`
and `build/` directories.

**Root cause (my understanding):** the skip patterns are matched as substrings
with leading slashes (e.g. `"/node_modules/"`), so a top-level path like
`node_modules/lib/index.js` (no leading slash) is not matched and its `.js`
files get counted. Planned fix: match on path *segments* instead of
slash-wrapped substrings.

**Validation targets:** `test_node_modules_excluded` and
`test_build_directory_excluded` in `tests/unit/test_tech_detector.py` (currently
failing).

**Out of scope (noted for a possible separate issue):** primary language is
selected alphabetically (`sorted(languages)[0]`), not by file count, despite the
"most common" comment. Not needed to satisfy #150; keeping this PR focused.