## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/159

### Understand

**Root cause:** structlog is left at its *default* configuration during test runs. The default uses `structlog.PrintLogger`, which writes rendered events straight to `stdout` and never propagates them through Python's stdlib `logging` system. pytest's `caplog` fixture only captures records that flow through stdlib `logging`, so `caplog.text` and `caplog.records` are always empty.

The project already has correct routing in `core/logging.py::configure_logging()`. That function calls `structlog.configure(..., logger_factory=structlog.stdlib.LoggerFactory())`, which sends events through stdlib `logging`. The problem is that **nothing calls `configure_logging()` during tests** (there is no structlog setup in `tests/conftest.py`), so the default config is what's active.

- **Expected:** A `logger.warning(...)` emitted by application code is captured by `caplog`, so `"Empty chunks list" in caplog.text` is `True`.
- **Actual:** The warning is printed to stdout (visible in pytest's "Captured stdout"), but `caplog.text == ''`, so the assertion fails with `AssertionError: assert ('Empty chunks list' in '' or False)`.

### Map

- `tests/conftest.py`: **primary change.** Add an `autouse`, session-scoped fixture that configures structlog to route through stdlib `logging` before any test logs.
- `core/logging.py::configure_logging()`: existing reference implementation. The fixture will reuse its `LoggerFactory()` approach (or call it directly with a test-appropriate renderer).
- `ingestion/embeddings/batch_processor.py:7`: the module under test. It uses `logger = structlog.get_logger()` and needs **no change**, since it already goes through the global structlog config.
- `tests/unit/test_batch_processor.py:36-44`: the failing test. It needs **no change** once routing is fixed.
- The 30+ other modules using `structlog.get_logger()` benefit automatically, with no per-module changes.

### Plan

1. **Add a structlog test fixture** in `tests/conftest.py`: an `autouse=True` fixture that calls `structlog.configure(...)` with `logger_factory=structlog.stdlib.LoggerFactory()`, `cache_logger_on_first_use=False`, and a plain (non-ANSI) renderer chain ending in `structlog.stdlib.ProcessorFormatter.wrap_for_formatter` / `ConsoleRenderer(colors=False)` so the event text lands in `caplog` cleanly.
2. **Ensure caplog visibility:** confirm the fixture (or the test) sets the capture level so WARNING-level records propagate to `caplog` (the default caplog handler captures propagated records; set `caplog.set_level`/root level if needed).
3. **Run the target test:** `python -m pytest tests/unit/test_batch_processor.py -v` and expect `11 passed`.
4. **Run the full suite:** `python -m pytest` to confirm no regressions from changing the global structlog config (watch for tests that assert on raw stdout instead of caplog).
5. **Commit** the reproduction and fix, then link the commit in `JOURNAL.md`.

### Inputs & outputs

- **Input:** the current pytest environment with structlog unconfigured.
- **Output/change:** a new fixture in `tests/conftest.py`. After the change, structlog log calls made anywhere in the codebase during tests are routed through stdlib `logging` and captured by `caplog`. `test_empty_chunks_list_returns_empty` passes, and all other `caplog`-based assertions across the suite work.

### Risks & unknowns

- **Global config bleed:** `structlog.configure()` is process-global. An `autouse` session fixture makes it deterministic, and using `cache_logger_on_first_use=False` avoids stale cached loggers from module-import time.
- **Renderer format:** if the renderer emits ANSI color codes, `caplog.text` substring checks could break, so use `colors=False` or a plain renderer in tests.
- **Level filtering:** `structlog.stdlib.filter_by_level` plus caplog's default level must allow WARNING through. Verify this with the full-suite run.
- **Unknown:** whether any existing passing test relies on the *default* stdout behavior. The full-suite run in step 4 will surface this.

### Edge cases

- Loggers created at module import time (before the fixture runs), handled by disabling logger caching so config is picked up on first log call.
- Log records at various levels (debug/info/warning/error). The batch processor emits all of these, and the config should route each to stdlib logging without dropping the message text.
- Tests that assert on `caplog.records[*].message` versus `caplog.text`. Both must be populated, so the message string emitted to the stdlib logger must contain the event text.
- Exception logging (`logger.error(..., error=str(e))`) paths in `batch_processor.process`, which should still render and be capturable.
