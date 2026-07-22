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
