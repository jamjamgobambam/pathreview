## Solution plan

**Issue:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

### Understand

PathReview application code logs through `structlog.get_logger()` (for example
`BatchEmbeddingProcessor.process([])` in `ingestion/embeddings/batch_processor.py`
calls `logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")`).
Unit tests such as
`tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`
assert that those messages appear in pytest's `caplog` fixture
(`caplog.text` or `caplog.records`).

**Expected:** The warning is emitted and visible to `caplog`, so the assertion
passes.

**Actual:** The warning prints to stdout (visible in pytest's "Captured stdout
call"), but `caplog.text` is empty and `caplog.records` has no matching entries,
so the assertion fails.

**Root cause:** Production logging is configured in `core/logging.py` via
`configure_logging()`, which is not invoked during the unit-test session.
`tests/conftest.py` does not configure structlog to propagate into the stdlib
logging system that `caplog` hooks. Until that bridge exists in test setup,
every `caplog`-based log assertion will fail even when the code under test
logs correctly.

### Map

Files and modules involved:

- **`tests/conftest.py`** (primary change) — add session/autouse fixture (or
  module-level configure) that wires structlog into stdlib logging for tests.
- **`core/logging.py`** (reference only) — production `configure_logging()` and
  `cache_logger_on_first_use=True`; do not change unless the test-only approach
  proves insufficient.
- **`tests/unit/test_batch_processor.py`** — verification target
  (`test_empty_chunks_list_returns_empty`); assertions should pass unchanged.
- **`ingestion/embeddings/batch_processor.py`** — call site that emits the
  warning; no production change expected.

### Plan

1. ~~In `tests/conftest.py`, add a pytest fixture (prefer `autouse=True`, session
   or function scope) that configures structlog with
   `structlog.stdlib.LoggerFactory` and a processor chain that emits through
   stdlib logging (for example `ProcessorFormatter` /
   `wrap_for_formatter`), without calling or modifying production
   `configure_logging()` in `core/logging.py`.~~
   **Done (Week 9):** Configured at **import time** in `tests/conftest.py` with
   `LoggerFactory`, `BoundLogger`, `cache_logger_on_first_use=False`, and
   `ConsoleRenderer`, plus an autouse fixture that keeps caplog/root at INFO.
2. ~~Ensure test log levels allow warnings through to `caplog`.~~ **Done.**
3. ~~Re-run `test_empty_chunks_list_returns_empty` and confirm it passes.~~
   **Done** — passes unchanged.
4. ~~Run broader unit suite; remove reproduction docstring.~~ **Done** — added
   `tests/unit/test_structlog_caplog.py`; suite improved (52→51 failed,
   345→348 passed); remaining failures are pre-existing and unrelated.

### Inputs & outputs

**Input:** structlog log events from code under test — e.g.
`logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")`
(event string plus any bound context kwargs).

**Output:** The same events available as stdlib `logging.LogRecord` instances
in `caplog.records`, with event text searchable via `caplog.text` and/or
`record.message`, so existing assertions like
`"Empty chunks list" in caplog.text` continue to work without rewriting tests.
Production logging behavior outside the test suite should be unchanged.

### Risks & unknowns

- **`cache_logger_on_first_use=True` in `core/logging.py`:** Loggers created at
  import time may ignore a late `structlog.configure()` in a fixture.
  Investigate configuring at `conftest` import time vs fixture order if capture
  still fails after the first attempt.
- **Message shape vs assertions in `test_batch_processor.py`:** Console or JSON
  renderers may put the event string in `record.msg` / `record.getMessage()`
  differently than a plain `"Empty chunks list" in caplog.text` check expects.
  Verify the exact `record.message` / `caplog.text` content after wiring.
- **Scope creep into production:** Keep changes in `tests/conftest.py`; only
  touch `core/logging.py` if test-only configuration cannot make `caplog` work.

### Edge cases

- Empty chunks list (`process([])`) — the known failing warning path.
- Non-empty successful `process(chunks)` — info logs may fire; tests that do
  not use `caplog` must still pass.
- Tests that never log — the new fixture must be a no-op for them (no failures,
  no noisy side effects).
- Default `caplog` / root log-level filtering — warnings must be captured;
  behavior when only INFO (or DEBUG) events are emitted should still be
  predictable if levels are set deliberately in the fixture.
