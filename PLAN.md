## Solution plan

**Issue:** structlog output is not captured by pytest caplog — log assertions fail suite-wide (#159)
https://github.com/ascherj/pathreview/issues/159

### Understand
Root cause: structlog is configured to render logs directly (e.g. to stdout) but is not wired to propagate into Python's standard `logging` module. Pytest's `caplog` fixture only captures records that pass through stdlib `logging`, so any test asserting on `caplog.text` or `caplog.records` fails, even though the log event genuinely occurred. Expected behavior: log calls made through structlog should also be visible to `caplog`. Actual behavior: `caplog.text` is empty even when the log line is printed.

### Map
- `tests/conftest.py` — likely needs a fixture or global structlog configuration that adds stdlib propagation (e.g. `structlog.stdlib.ProcessorFormatter` or `structlog.testing.capture_logs`)
- `tests/unit/test_batch_processor.py` — the specific failing test used to verify the fix
- Possibly a structlog config module (e.g. `core/logging.py` or similar) if structlog is configured globally rather than per-test

### Plan
1. Locate where structlog is currently configured (likely in a core config or `conftest.py`) to understand the existing processor chain
2. Add a stdlib-logging-compatible processor (e.g. `structlog.stdlib.ProcessorFormatter.wrap_for_formatter`) so structlog output also flows into stdlib `logging`
3. Confirm the fix doesn't break structlog's normal console output during real app usage (not just tests)
4. Run the originally failing test to confirm `caplog` now captures the log line
5. Run the full test suite to check for other tests relying on `caplog` that may now pass or behave differently

### Inputs & outputs
Input: structlog log calls made anywhere in the app during test execution. Output: those log records should appear in `caplog.text` / `caplog.records` during pytest runs, without changing structlog's behavior outside of tests.

### Risks & unknowns
- Might accidentally cause duplicate log output (once via structlog's normal renderer, once via stdlib propagation) if not scoped carefully
- Unsure yet whether the fix needs to be global (conftest.py, affecting all tests) or applied per-test-file
- Need to verify this doesn't slow down the test suite significantly if applied globally

### Edge cases
- Tests that don't use `caplog` at all should be unaffected
- Structlog calls made outside of a test context (e.g. during real app requests) should still log normally
- Multiple structlog loggers/modules should all propagate consistently, not just the one used in `batch_processor.py`
