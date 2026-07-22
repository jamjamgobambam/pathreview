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

### "Is this right for me?" — selection notes

Worked through the checklist before claiming the issue:

- **Open and unassigned?** Yes — no one is assigned, so I'm not duplicating work.
- **Labeled for my level?** Yes — `tier-1` **and** `good first issue`; appropriate
  as a first contribution to a large codebase.
- **Can I reproduce it?** Yes — cloned, set up locally, and the two named tests
  (`test_node_modules_excluded`, `test_build_directory_excluded`) fail exactly as
  the issue describes; the issue's manual repro also reproduces (`primary_language`
  comes back `JavaScript` instead of `Python`).
- **Is the scope contained?** Yes — the bug lives in a single method
  (`_should_skip_file`) in one file (`agent/tools/tech_detector.py`), ~10 lines.
- **Clear acceptance criteria?** Yes — two failing tests define "done"; I code to
  a target rather than guessing intent.
- **Do I understand the root cause?** Yes — slash-wrapped substring matching
  misses top-level directories (documented in Working notes below).
- **Does it need deep domain knowledge?** No — it's string/path handling, not RAG
  or agent internals, so it's tractable without understanding the whole system.

**Scope reasoning:** I'm keeping this PR to *only* the vendored/build exclusion
bug. While investigating I found a second, separate defect — primary language is
selected alphabetically (`sorted(languages)[0]`) rather than by file count,
despite the "most common" comment — but fixing the exclusion logic alone
satisfies both acceptance tests, and bundling an unrelated behavior change would
work against a clean, reviewable first PR. I've noted the counting bug as a
candidate for a separate issue.

---

## Week 8 — Reproduction & solution plan

**Issue:** [#150](https://github.com/ascherj/pathreview/issues/150) — Tech
detector counts vendored and build-output files, skewing language detection

**Reproduced locally?** [x] Yes — reliably

**Reproduction steps:**
```bash
# Failing tests (acceptance target):
.venv/bin/pytest tests/unit/test_tech_detector.py \
  -k "node_modules_excluded or build_directory_excluded" -v
#   -> both FAIL: assert primary_language == "Python" but got "JavaScript"

# Manual repro from the issue:
.venv/bin/python -c "from agent.tools.tech_detector import TechDetector; \
print(TechDetector().execute({'files': \
['main.py','core/app.py','node_modules/lib/a.js','node_modules/lib/b.js', \
'node_modules/x/c.js','node_modules/y/d.js','build/bundle.js','build/vendor.js']}) \
.data['primary_language'])"
#   -> before fix: 'JavaScript'  (expected 'Python')
```

**Where the bug lives:** `agent/tools/tech_detector.py`, method
`_should_skip_file()` (~L143–164) — it matches skip patterns as slash-wrapped
substrings (`"/node_modules/"`), so top-level `node_modules/` and `build/` paths
(no leading slash) are not excluded.

**Solution plan:** see [PLAN.md](PLAN.md). Summary: match on path *segments*
(`filepath.split("/")`) against a set of skip-dir names, covering top-level and
nested vendored/build dirs.

**Files I'll touch:** `agent/tools/tech_detector.py` (one method). No test
changes — the two failing tests define "done".

**Risks / unknowns:** possible over-exclusion of an oddly-named source file (low
impact — no language extension); Windows `\` paths out of scope; ~51 unrelated
pre-existing suite failures are not caused by this change.

**Status:** reproduction confirmed and fix implemented on this branch (commit
`f413972`); all `tech_detector` tests pass.

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