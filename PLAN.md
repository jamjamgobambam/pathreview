## Solution plan

**Issue:** [#159 — structlog output is not captured by pytest caplog — log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

### Understand
The application logs through `structlog`, but nothing wires structlog into the
standard library `logging` system during tests. `configure_logging()` in
[core/logging.py](core/logging.py) *does* set up a stdlib `LoggerFactory`, but
it is only called at app startup — the test suite never invokes it. As a
result, structlog uses its **default** configuration, which renders events with
a `PrintLogger` that writes directly to stderr and bypasses stdlib `logging`
entirely.

pytest's `caplog` fixture only sees records that flow through the stdlib
`logging` system (it attaches a handler to the root logger). Because structlog
never emits stdlib `LogRecord`s in tests, `caplog.text` / `caplog.records` are
empty.

- **Expected:** a test that triggers a log event (e.g. the "Empty chunks list"
  warning in [ingestion/embeddings/batch_processor.py:40](ingestion/embeddings/batch_processor.py#L40))
  can assert on it via `caplog`.
- **Actual:** the warning is visibly printed to stderr, but `caplog` is empty,
  so `test_empty_chunks_list_returns_empty` fails — along with every other
  `caplog`-based assertion in the suite.

### Map
Files involved:
- [tests/conftest.py](tests/conftest.py) — **primary change**: add an autouse
  fixture that configures structlog to route through stdlib `logging` so
  `caplog` captures events.
- [core/logging.py](core/logging.py) — reference for the production processor
  chain (`structlog.stdlib.LoggerFactory`, `filter_by_level`, etc.); the test
  config should mirror it closely enough to be representative.
- [tests/unit/test_batch_processor.py](tests/unit/test_batch_processor.py) —
  the failing test (`test_empty_chunks_list_returns_empty`) used to verify the
  fix; no change expected, but it validates the outcome.
- [ingestion/embeddings/batch_processor.py](ingestion/embeddings/batch_processor.py) —
  the module under test that emits the log; module-level
  `logger = structlog.get_logger()` interacts with structlog caching (see Risks).

### Plan
1. Add an `autouse=True` fixture (session- or function-scoped) in
   [tests/conftest.py](tests/conftest.py) that calls `structlog.configure(...)`
   with `logger_factory=structlog.stdlib.LoggerFactory()` and a processor chain
   ending in `structlog.stdlib.render_to_log_kwargs` (or a
   `ProcessorFormatter`) so events become real stdlib `LogRecord`s.
2. Set `cache_logger_on_first_use=False` in the test config so module-level
   loggers already imported (e.g. in `batch_processor.py`) pick up the test
   configuration rather than a frozen default.
3. Ensure levels are permissive enough for `caplog` (e.g. `caplog.set_level`
   or a filtering wrapper at `NOTSET`) so both `warning` and `info` events are
   captured, and confirm root-logger propagation is on.
4. Run `pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q`
   to confirm it passes, then run the full suite to confirm no regressions and
   that other `caplog`-based tests now pass.

### Inputs & outputs
- **Input:** the existing pytest run and structlog's global configuration state.
- **Output:** a test-only structlog configuration (in `conftest.py`) that emits
  stdlib `LogRecord`s. `caplog.text` and `caplog.records` become populated, so
  log assertions pass. No production code or runtime logging behavior changes.

### Risks & unknowns
- **Logger caching:** `batch_processor.py` binds `logger` at import time and
  `core/logging.py` uses `cache_logger_on_first_use=True`. If a cached logger is
  created before the test config runs, config changes are ignored. Mitigate by
  disabling caching in the test config and configuring before the first log call
  (autouse fixture).
- **Global config leakage:** `structlog.configure()` is process-global. If any
  test (or app startup path) calls `configure_logging()` it could override the
  test config; the autouse fixture ordering must ensure the test config wins for
  each test.
- **Level filtering:** `filter_by_level` plus stdlib root level could drop
  `info`/`debug` events; need to confirm captured level matches what tests assert.
- Whether to reuse `configure_logging()` directly vs. a dedicated test config —
  leaning toward a dedicated test config to keep `render_to_log_kwargs` /
  caching concerns isolated to tests.

### Edge cases
- Tests that assert on different levels (`warning` vs `info` vs `debug`).
- Tests that use structlog key/value context (`chunk_count=...`) — confirm those
  render into `caplog.text` or are reachable via `record`.
- Multiple tests in one session each expecting a clean `caplog` (no cross-test
  bleed of records).
- Tests that assert *no* log was emitted (config must not fabricate records).
- Interaction with `structlog.testing.capture_logs` if any test uses it instead
  of `caplog`.
