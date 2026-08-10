## Solution plan

**Issue:** structlog output is not captured by pytest caplog — log assertions fail suite-wide
https://github.com/ascherj/pathreview/issues/159

### Understand
structlog is configured to emit logs (confirmed via stdout: "[warning] Empty chunks list
provided to BatchEmbeddingProcessor"), but it never propagates into Python's stdlib `logging`
module. pytest's `caplog` fixture only captures records that pass through stdlib `logging`,
so `caplog.text` stays empty even though the log genuinely fired. Expected behavior: caplog
should capture structlog-emitted log events. Actual behavior: caplog sees nothing.

### Map
- `tests/conftest.py` — currently has no logging/structlog configuration; this is where the
  fix needs to live (likely a fixture or `pytest_configure` hook)
- `tests/unit/test_batch_processor.py` — contains the failing test
  (`test_empty_chunks_list_returns_empty`) used to verify the fix
- Possibly a `core/` logging setup file, to check how structlog is configured in production
  so the test config mirrors it

### Plan
1. Locate how structlog is configured in the app itself (check `core/` for a logging config
   module) to understand the existing processor chain
2. Add a fixture or global config in `tests/conftest.py` that wires structlog's output into
   stdlib `logging`, using `structlog.stdlib.ProcessorFormatter` (or
   `structlog.testing.capture_logs`)
3. Run the failing test to confirm `caplog.text` now captures the log line
4. Run the full test suite (`pytest`) to check for any other tests relying on `caplog` that
   are affected by this change (positively or negatively)
5. Clean up / add a comment explaining the fixture's purpose for future contributors

### Inputs & outputs
Input: structlog log calls made anywhere in the app during test execution.
Output: those log records become visible via pytest's `caplog.text` and `caplog.records`,
so any test asserting on them passes when the expected log event fires.

### Risks & unknowns
- Not yet confirmed how structlog is configured in production code — if the processor chain
  is complex, mirroring it in tests could require more than a simple fixture
- Risk of breaking other tests if the fixture changes log level or formatting in a way other
  tests unintentionally depend on
- Unsure yet whether the fix should be a global `autouse` fixture in `conftest.py` or applied
  per-test — need to check if any tests intentionally rely on the current (broken) behavior

### Edge cases
- Tests that don't use `caplog` at all shouldn't be affected by the fix
- Log calls made at different levels (debug, info, warning, error) should all propagate
  correctly, not just warning-level ones
- Structured log fields (e.g. key-value pairs structlog attaches) shouldn't break stdlib
  logging's plain-text formatting