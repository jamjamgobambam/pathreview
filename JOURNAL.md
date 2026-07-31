# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The app configures `structlog` for logging across most of the codebase (`core/logging.py`, plus `api/`, `agent/`, `rag/`, `ingestion/`, and `safety/`), but the test suite's `tests/conftest.py` never bridges structlog back into the standard library `logging` module that pytest's `caplog` fixture relies on. As a result, any test that asserts on `caplog.text` or `caplog.records` fails even when the code under test logs exactly what's expected — the log lines are being emitted, just not where `caplog` can see them. `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty` is a concrete example: it checks for an "empty" log message via `caplog`, and fails today even though the batch processor does log it. A successful fix configures structlog (via `structlog.stdlib` processors or `structlog.testing.capture_logs`) in `conftest.py` so `caplog`-based assertions work suite-wide, not just for this one test.

**Scope reasoning ("Is this right for me?"):**
- Single-file fix (`tests/conftest.py`), no schema, API, or cross-service changes — low blast radius for a first contribution.
- Clear, reproducible failure (`pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q`) and a clear pass/fail signal once fixed.
- Tier 1 / "good first issue" labeled, matching my experience level with this codebase.
- Touches a pattern (structlog + pytest caplog) that's well documented externally, so it's learnable without deep prior context on PathReview internals.

**Branch name:** fix/159-caplog-structlog-config

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [ff9b8b1 — docs(#159): document caplog/structlog repro in conftest](https://github.com/koechio/pathreview/commit/ff9b8b1)

**Reproduction summary:**
Ran `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty` and confirmed it fails with `caplog.text == ''` even though the warning is visible under "Captured stdout call" — structlog never calls `configure_logging()` in the test process, so its output never reaches the stdlib root logger that `caplog` attaches to.

**PLAN.md link:** [PLAN.md](https://github.com/koechio/pathreview/blob/fix/159-caplog-structlog-config/PLAN.md)

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Still deciding fixture scope (session vs. function) for the structlog bridge in `tests/conftest.py`, and need to confirm `cache_logger_on_first_use` won't let a module cache a pre-fixture logger. Details in PLAN.md's Risks & unknowns section.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: added an autouse, function-scoped `configure_structlog_for_tests` fixture in `tests/conftest.py` that calls `structlog.configure(...)` with `logger_factory=structlog.stdlib.LoggerFactory()` and `cache_logger_on_first_use=False`, mirroring the processor chain in `core/logging.py::configure_logging()` but rendering to a plain string via `KeyValueRenderer` instead of JSON/console output. Resolved the two open risks from Week 8: chose function-scoped (not session-scoped) specifically so `cache_logger_on_first_use=False` can't let a module-level logger cache a pre-fixture configuration. Verified `test_empty_chunks_list_returns_empty` now passes, and added `tests/unit/test_logging_conftest.py` with three tests exercising the fixture directly (event text in `caplog.text`, correct `levelname` in `caplog.records`, and bound context via `.bind()`) to prove the fix is suite-wide and not special-cased to the batch processor. Ran the full unit suite before and after: 53 failed/375 passed → 52 failed/379 passed — the only failure that flipped is the target test, and the remaining 52 are pre-existing failures unrelated to #159 (confirmed same test names in both runs).

**Next steps:**
Run `make check` (ruff/black/mypy) to self-review against CONTRIBUTING.md, open a draft PR for peer/mentor feedback in Slack, then mark ready for review and submit Check-in 2.

**Blockers:**
None.
