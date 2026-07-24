## Solution plan

**Issue:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide #159](https://github.com/ascherj/pathreview/issues/159)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

- **Root cause:** `BatchEmbeddingProcessor` logs with `structlog.get_logger()`. In tests, structlog is never configured to feed the stdlib logging system, so events go through structlog's default print path (visible on stdout) and never become `logging.LogRecord`s. pytest's `caplog` fixture only sees stdlib records, so `caplog.text` / `caplog.records` stay empty.
- **Actual behavior:** Running the repro test fails. The warning is printed to stdout, but the assertion on `caplog` fails because `caplog.text == ''`.
- **Expected behavior:** The same warning is visible to `caplog`, so assertions like `"Empty chunks list" in caplog.text` pass. Production logging via `core.logging.configure_logging()` stays unchanged.

**Repro command:**
```bash
.venv/bin/pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -v
```

**What I saw (2026-07-23):**
- Test result: FAILED
- Captured stdout: `Empty chunks list provided to BatchEmbeddingProcessor`
- Assertion error: `assert ('Empty chunks list' in '' or False)` where `''` is `caplog.text`

### Map
Which files, functions, or modules are involved? List the specific files you expect to touch.

- **Files to modify:**
  - `tests/conftest.py` — configure structlog for the test session so events propagate into stdlib logging that `caplog` can capture
- **Reference / verify only (not changing product logging):**
  - `ingestion/embeddings/batch_processor.py` — emits `logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")`
  - `tests/unit/test_batch_processor.py` — `test_empty_chunks_list_returns_empty` asserts on `caplog`
  - `core/logging.py` — production/dev `configure_logging()`; use as a reference for stdlib integration, do not change unless a shared helper is clearly needed

### Plan
What are the steps to fix this issue? Break it into 3–5 concrete sub-tasks.

1. **Confirm root cause in conftest:** Note that `tests/conftest.py` has no structlog setup today, and only this unit test currently asserts on `caplog`.
2. **Add test-only structlog config:** In `tests/conftest.py`, add an autouse fixture (or session setup) that configures structlog with `structlog.stdlib.LoggerFactory()`, stdlib processors, and `ProcessorFormatter.wrap_for_formatter` (or an equivalent path that creates real `LogRecord`s). Reset defaults after tests if needed so config does not leak.
3. **Wire log levels for caplog:** Ensure warning-level events are captured (e.g. default level or `caplog.at_level` / root logger level) so the empty-chunks warning is recorded.
4. **Verify the reported test:** Re-run `test_empty_chunks_list_returns_empty` and confirm it passes with the warning present in `caplog.text` or `caplog.records`.
5. **Sanity check nearby unit tests:** Run `tests/unit/test_batch_processor.py` (and a quick broader `make test-unit` if cheap) to make sure the new logging config does not break unrelated tests.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Inputs:** Existing structlog warning calls in application code; pytest `caplog` fixture.
- **Outputs:** Test-session structlog configuration in `tests/conftest.py` so `caplog` receives those events. No change to batch processor behavior or production log format.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- **Riskiest part:** Getting the processor chain right. If the last processor still renders and prints without going through stdlib, stdout will look fine but `caplog` will stay empty (same bug).
- **Config bleed:** `cache_logger_on_first_use=True` in production config means loggers bound before reconfigure can keep old behavior. Need to configure early (autouse fixture / pytest_configure) and possibly reset.
- **Unknown:** Whether calling `core.logging.configure_logging()` alone is enough for `caplog`, or whether tests need a dedicated, quieter formatter. I will try a test-specific stdlib setup first so we do not couple tests to app env settings.
- **Competition:** Others also claimed #159. Keep the diff small so a clean PR can land.

### Edge cases
What inputs or states should your fix handle gracefully?

- Empty `caplog` when nothing was logged (tests that do not log should still see empty records).
- Warning vs info vs error levels used by other modules if more `caplog` tests appear later.
- Tests that import modules which call `structlog.get_logger()` at import time (logger caching).
- Do not require changing every logger call site; the fix belongs in test bootstrap, not in `batch_processor.py`.
