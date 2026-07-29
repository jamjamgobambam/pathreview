## Solution plan

**Issue:** [#159 - structlog output is not captured by pytest caplog — log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

### Understand
- **Expected:** `caplog`-based assertions (e.g. `assert "Empty chunks list" in caplog.text`) should see log events emitted via `structlog.get_logger()` calls in application code.
- **Actual:** They fail suite-wide, even though the log line is visibly printed (confirmed by reproducing `test_empty_chunks_list_returns_empty` — `caplog.text` is `''` while stdout shows `2026-07-28 ... [warning] Empty chunks list provided to BatchEmbeddingProcessor`).
- **Root cause:** [core/logging.py](core/logging.py) defines `configure_logging()`, which wires structlog into the stdlib `logging` module (`logger_factory=structlog.stdlib.LoggerFactory()` + `logging.basicConfig(...)`). But `configure_logging()` is only ever called from [scripts/seed_db.py](scripts/seed_db.py) — it's never invoked during the test session. Without it, structlog falls back to its own default global config: `PrintLoggerFactory` + plain `BoundLogger`, which renders and **prints directly to stdout**, completely bypassing the stdlib `logging` module. Since pytest's `caplog` fixture only captures records that pass through stdlib `logging` handlers, it never sees anything.

### Map
- [tests/conftest.py](tests/conftest.py) — add an autouse fixture to configure structlog for the test session (currently only has unrelated data fixtures).
- [core/logging.py](core/logging.py) — reference for the processor chain shape (`configure_logging`); test config should mirror it but route through `ProcessorFormatter` instead of a renderer, and use `structlog.stdlib.BoundLogger` as the wrapper class so log calls reach real `logging.Logger` records.
- [tests/unit/test_batch_processor.py](tests/unit/test_batch_processor.py) — existing failing test used to verify the fix (`test_empty_chunks_list_returns_empty`); no changes expected here if the fix is done correctly.
- Any other test file asserting on `caplog` against structlog-emitted logs (grep for `caplog` under `tests/`) should be checked once the fixture is in place.

### Plan
1. In `tests/conftest.py`, add an autouse, session- or function-scoped fixture (e.g. `configure_structlog_for_tests`) that calls `structlog.configure(...)` with:
   - `processors=[..., structlog.stdlib.ProcessorFormatter.wrap_for_formatter]` (same pre-processing chain as `core/logging.py`, but ending in `wrap_for_formatter` instead of `ConsoleRenderer`/`JSONRenderer`), so the final message reaches a real stdlib `LogRecord`.
   - `logger_factory=structlog.stdlib.LoggerFactory()` and `wrapper_class=structlog.stdlib.BoundLogger`, so `structlog.get_logger()` calls proxy into real `logging.Logger` instances.
   - `cache_logger_on_first_use=False` (or call this fixture with `autouse=True` before any logger is cached) to avoid stale loggers from a prior configuration leaking across tests.
2. Make sure the fixture doesn't require formatting output to be readable — caplog only needs records to exist on the root/propagated logger; a bare `ProcessorFormatter.wrap_for_formatter` is sufficient without attaching a formatter/handler ourselves, since pytest's own `LogCaptureHandler` is already attached to the root logger.
3. Restore/reset structlog's configuration after each test (or scope the fixture appropriately) so test-only config doesn't bleed into other test modules or leave global state mutated between runs — use `structlog.reset_defaults()` in fixture teardown, or configure once per session if isolation isn't required.
4. Run `pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q` to confirm it now passes.
5. Run the full suite (`pytest -q`) to confirm no regressions and that other `caplog`-dependent tests (if any) also pass.

### Inputs & outputs
- **Input:** structlog log calls made via `structlog.get_logger()` throughout application code under test (e.g. `logger.warning(...)`, `logger.info(...)`).
- **Output:** Those events become real stdlib `logging.LogRecord`s visible to pytest's `caplog` fixture (`caplog.text`, `caplog.records`), without changing any production logging behavior in `core/logging.py` or requiring test files to switch to `structlog.testing.capture_logs()`.

### Risks & unknowns
- `cache_logger_on_first_use=True` (used in production config) can cause a logger fetched by one test to keep a stale processor chain if another module configures structlog differently later — need to confirm no other place in the codebase calls `structlog.configure()` during test collection that could race with the conftest fixture.
- Default caplog capture level is `WARNING` in some pytest versions/configs — need to verify INFO/DEBUG-level structlog calls in other tests (if any) require `caplog.set_level(...)`; this is a pytest-level concern separate from the structlog wiring itself, but worth checking after the fix so the fixture doesn't need a `level=logging.DEBUG` default that's overly broad.
- Since `configure_logging()` (prod) and the new test fixture both call `structlog.configure(...)` globally, order-of-import between conftest and any code path that might call `configure_logging()` during tests (currently none do) should be double-checked so tests don't accidentally trigger production JSON/console rendering.

### Edge cases
- Tests that don't use `caplog` at all should be unaffected (no behavior change when the fixture is present but the test doesn't inspect logs).
- Tests running in parallel (if `pytest-xdist` is used) — structlog global configuration is process-global; confirm this doesn't cause cross-test interference within a worker (should be fine since each worker is a separate process).
- Log calls using structlog's keyword-argument style (`logger.warning("msg", key=value)`) should still produce a `record.message`/`caplog.text` that contains the original event string, not just the structured kwargs — verify via the existing test's dual assertion (`"Empty chunks list" in caplog.text or any(... in record.message ...)`).
