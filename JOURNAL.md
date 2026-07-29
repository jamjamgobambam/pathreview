# Development Journal

## Environment Setup

- **OS:** Windows 11 (Git Bash)
- **Python:** 3.11+ (project venv at `.venv/`)
- **Node.js / npm:** 18+ / 9+
- **Docker:** backing services (PostgreSQL on `5433`, Redis on `6379`) via `docker compose up -d`

### Setup verified

- `docker compose up -d` — `db` and `redis` containers healthy
- `alembic upgrade head` — migrations applied against Postgres on port 5433
- `scripts/seed_db.py` — seeded the three sample accounts (`user1..3@example.com`)
- Frontend dependencies installed (`cd frontend && npm install`)
- Backend reachable at http://localhost:8000/docs, frontend at http://localhost:5173

### Notes

- On Windows, force UTF-8 output (`PYTHONUTF8=1`) so the seed script's Unicode
  status glyphs don't crash on the cp1252 console codepage.
- `LLM_PROVIDER=mock` is the default and requires no API key for local development.

## Work Log

- Set up local development environment and verified the full stack runs.
- Created branch `test/156-readme-scorer-fixture-word-count` for issue #156
  (README scorer test fixture too short for its word-count assertion).

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `readme_scorer` agent tool assigns a README a `word_count` and a
`word_count_category` (e.g. "comprehensive") based on how long the README is.
Its unit test `test_readme_with_all_quality_signals` claims to exercise the
"comprehensive" path, asserting `word_count > 100` and
`word_count_category == "comprehensive"`, but the fixture README it feeds in
is only ~51 words long. The scorer behaves correctly and returns 51, so the
assertion `51 > 100` fails — the test, not the code, is wrong. A successful
fix extends the fixture README past 100 words (or corrects the assertion) so
the test genuinely validates the comprehensive-length branch it was meant to
cover. This lives in `tests/unit/test_readme_scorer.py` against the
`agent` scorer tool.

**Branch name:** test/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Reproduction

Ran the test suite for the scorer to confirm the failure is real and matches
the issue report:

```
$ pytest tests/unit/test_readme_scorer.py -q
...
>       assert data["word_count"] > 100
E       assert 51 > 100

tests/unit/test_readme_scorer.py:56: AssertionError
--- Captured stdout ---
readme_scored  category=minimal score=0.8717142857142858 word_count=51

1 failed, 22 passed in 0.33s
```

**Observed:** `test_readme_with_all_quality_signals` fails at the assertion
`data["word_count"] > 100` because the fixture README scores `word_count=51`.
The scorer also reports `category=minimal`, so the later
`word_count_category == "comprehensive"` assertion would fail too.

**Diagnosis:** The scorer is correct — the ~51-word fixture genuinely is not
"comprehensive". The bug is in the test's expectations, not the tool. Fix is
to extend the fixture past 100 words (or correct the assertion) so the test
validates the comprehensive-length branch it intends to.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sayalibadole/pathreview/commit/82fafcc0b25e71cc22876e7b0a10a54bcb25c3a3

**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` and observed
`test_readme_with_all_quality_signals` fail with `assert 51 > 100` — the
scorer correctly reports `word_count=51` / `category=minimal`, confirming the
fixture is too short for its own assertions (test bug, not a scorer bug).

**PLAN.md link:** https://github.com/sayalibadole/pathreview/blob/test/156-readme-scorer-fixture-word-count/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
The scorer only labels a README `"comprehensive"` at **≥ 500 words**, so the
fixture must reach 500 (not merely >100) to satisfy both assertions — I've
planned for this. One open question for review: the issue allows either
extending the fixture or correcting the assertion; I chose to extend the
fixture to preserve the test's intent, but I'll defer to maintainer preference
if feedback differs.
