# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`tests/unit/test_review_service.py` builds its mock `AsyncSession` so that `result.scalars()` returns a coroutine instead of a `MagicMock` result object. The service code in `review_service.py` correctly awaits `db.execute(...)`, but then calls the synchronous `.scalars().first()` / `.scalars().all()` on the returned object — since that object is itself an un-awaited coroutine, those calls raise `AttributeError: 'coroutine' object has no attribute 'first'` (and `'all'`). Running `pytest tests/unit/test_review_service.py -q` locally reproduces this exactly: 13 failed, 6 passed. The fix is entirely in the test file's mock setup — mock `db.execute` as an `AsyncMock` that resolves to a plain `MagicMock` result object (with `.scalars().first()`/`.scalars().all()` wired synchronously), rather than mocking `scalars()` itself as async. A successful fix makes all 19 tests in that file pass without touching the (already-correct) service code.

**Selection reasoning:**
This is my first time contributing to a codebase of this size, so I stayed in Tier 1 ("good first issue") rather than reaching for Tier 2/3 — I wanted a first PR that teaches me the repo's testing conventions without requiring me to understand the RAG/agent architecture end-to-end. Within Tier 1 I compared several candidates (async mock bugs, regex/pattern bugs in the ingestion and safety layers, doc gaps) using the "Is this right for me?" checklist and picked #158 because: (1) scope is contained to one test file (`tests/unit/test_review_service.py`) — no service code, migrations, or frontend changes required; (2) it's fully reproducible and verifiable without the full Docker stack (`pytest tests/unit/test_review_service.py -q`), so I can confirm the fix myself instead of relying on manual UI testing; (3) it had the least contention of the open Tier 1 issues (15 "I'll work on this" comments vs. 30-47 on several others), lowering the odds of colliding with another student's PR; (4) the bug (mocking `scalars()` as async instead of `execute()`) is a specific, well-documented async-mocking gotcha, so fixing it teaches me something reusable rather than being a one-off fixture edit.

**Branch name:** fix/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [fill in after you push — link to the commit that adds this Week 8 entry + PLAN.md]

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py -q` on the `fix/158-review-service-async-mocks` branch and observed **13 failed, 6 passed**. Every failure is `AttributeError: 'coroutine' object has no attribute 'first'` / `'all'`, raised at `core/services/review_service.py:47` and `:65` — confirming the mocked result's `scalars()` returns an un-awaited coroutine because the test builds it as an `AsyncMock`, while the (correct) service code calls the synchronous `.scalars().first()/.all()` on it.

**PLAN.md link:** [link to PLAN.md on this branch, e.g. https://github.com/amit-tzadok/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md]

**Walkthrough video (recommended):** [optional Loom link, ≤2 min — or leave blank]

**Blockers or open questions:**
Deciding between a minimal per-test fix (swap `AsyncMock()` → `MagicMock()` in each of the 13 tests) and refactoring the mock setup into a shared helper/fixture to prevent the mistake recurring. Leaning toward the shared helper, but want to confirm it doesn't disturb the 6 already-passing `create_review` tests.
