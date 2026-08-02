## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for `core/services/review_service.py` is below 40%

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review service orchestrates the full review workflow and is the most critical service in the application, but most of its code paths are untested. Add unit tests targeting the major execution paths including success, partial failure, and full failure cases.

Relevant files:

tests/unit/test_review_service.py



**Branch name:** test/109-test-coverage-service

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** <!-- paste your commit URL here after committing -->

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_review_service.py --cov=core.services.review_service --cov-report=term-missing` against the current `test/109-test-coverage-service` branch. Measured coverage on `core/services/review_service.py` is **22%** (135 statements, 105 missed) — even lower than the "below 40%" the issue reports. The uncovered ranges (`98–194`, `202–279`, `288`, `323`, `369–390`) confirm that `process_review` and all four internal helpers are entirely untested. A secondary finding: **13 of the 19 pre-existing tests fail** with `AttributeError: 'coroutine' object has no attribute 'all'` because the existing scaffolding uses `AsyncMock` where SQLAlchemy 2.0's sync `result.scalars()` chain requires `MagicMock`. The full coverage report is included in the reproduction commit.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** <!-- optional Loom link -->

**Blockers or open questions:**
- The `chromadb/chroma:0.4.22` image pinned in `docker-compose.yml` fails to boot against NumPy 2.0 (`np.float_` removed). Doesn't block this issue since `review_service.py` doesn't touch the vector store, but it will need bumping before end-to-end runs.
- Whether to fix the pre-existing broken tests as part of this PR or in a separate one — currently planned to fix them in-place because otherwise the coverage numbers stay wrong.
- `_run_agent_orchestration` and `_run_rag_retrieval_generation` are placeholder stubs; if real implementations land before this PR merges, the helper-level tests (step 4 of PLAN.md) will need to be revisited.