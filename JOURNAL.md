# Contribution Journal — PathReview (Module 3)

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's `tech_detector` tool infers a repository's primary programming
language from its file extensions, but it counts files it is supposed to ignore.
Its directory-skipping helper (`_should_skip_file`) matches patterns like
`"/node_modules/"` as slash-wrapped substrings, so top-level vendored or
generated folders such as `node_modules/` and `build/` slip through and the
third-party / bundled JavaScript inside them gets counted. The result is that a
mostly-Python repository can be misreported as JavaScript. A successful fix makes
the detector match on path *segments* instead, excluding those directories
whether they sit at the repo root or nested deeper, which turns the two provided
failing tests (`test_node_modules_excluded`, `test_build_directory_excluded`)
green. This lives in `agent/tools/tech_detector.py` in the Agent system.

**Branch name:** fix/150-exclude-vendored-build-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Working notes

### 2026-07-17 — Environment setup
- Started Docker backing services (`docker compose up -d`): Postgres (`:5433`),
  Redis (`:6379`), ChromaDB (`:8001`).
- Created `.env` from `.env.example` (`LLM_PROVIDER=mock`, no API key needed).
- Ran `make setup` (venv + deps + `alembic upgrade head` + seed + `npm install`).
- Ran `make run`; confirmed frontend at **http://localhost:5173** (HTTP 200) and
  API docs at http://localhost:8000/docs.
- Note: `/health` returns 503 from two pre-existing app-code bugs (Postgres check
  needs `text("SELECT 1")`; Redis check references a missing `redis_host`
  setting). Infra containers are healthy — unrelated to #150.

### 2026-07-17 — Fix for #150
- **Root cause:** `_should_skip_file` used slash-wrapped substring matching
  (`"/node_modules/" in filepath`), which fails for top-level paths like
  `node_modules/lib/x.js` (no leading slash), so those files were not excluded.
- **Fix:** match on path segments (`filepath.split("/")`) against a set of
  skip-dir names, covering both top-level and nested vendored/build directories.
- **Verification:** the two target tests pass; full
  `tests/unit/test_tech_detector.py` → 27 passed; the issue's exact repro now
  returns `Python`.
- **Out of scope (candidate for a separate issue):** primary language is chosen
  alphabetically (`sorted(languages)[0]`), not by file count, despite the "most
  common" comment. Not needed for #150; kept this PR focused.
- **Note on repo state:** the wider unit suite has ~51 pre-existing failures in
  unrelated modules (`skill_extractor`, `structural_chunker`, …) that also fail
  on `main`; they are not caused by this change.