# Solution plan

**Issue:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide (#159)](https://github.com/ascherj/pathreview/issues/159)

### Understand

The focused test calls `BatchEmbeddingProcessor.process([])`, which correctly returns an empty list and emits the expected warning. However, the test suite never configures structlog to use Python's standard logging system. Structlog therefore keeps its default `PrintLoggerFactory` and writes the rendered warning to stdout, while pytest's `caplog` fixture only observes standard logging records. The expected behavior is for test-time structlog events to reach standard logging so `caplog.text` or `caplog.records` contains the warning; the actual behavior leaves both empty and fails the assertion.

### Map

- `tests/conftest.py`: add shared, test-only structlog configuration and restore global state after the test session.
- `core/logging.py`: reference the application's existing stdlib-backed structlog configuration; no production change is currently planned.
- `ingestion/embeddings/batch_processor.py`: source of the warning used to reproduce the issue; no business-logic change is expected.
- `tests/unit/test_batch_processor.py`: existing focused regression test and `caplog` assertion; change only if an additional assertion is needed to verify capture behavior clearly.

### Plan

1. Add a test-session fixture or pytest lifecycle hook in `tests/conftest.py` that configures structlog with `structlog.stdlib.LoggerFactory` and processors compatible with standard logging capture.
2. Preserve the previous structlog configuration before changing it, disable first-use caching if needed, and restore the prior configuration after the test session to prevent global state leakage.
3. Run the focused reproduction test and confirm the warning appears in `caplog` while `process([])` still returns `[]`.
4. Run all tests in `tests/unit/test_batch_processor.py`, followed by the complete unit-test suite, to catch logging-format, isolation, or ordering regressions.
5. Keep the change limited to test infrastructure unless the regression results demonstrate that a production logging change is necessary.

### Inputs & outputs

The relevant input is a structlog warning emitted while pytest is running, demonstrated by passing an empty chunk list to `BatchEmbeddingProcessor.process([])`. The processor's return value must remain `[]`. The change should produce a standard logging record that pytest can expose through `caplog.text` and `caplog.records`, without changing application runtime logging outside tests.

### Risks & unknowns

- Structlog configuration is process-global, so a test fixture could affect unrelated tests or make results depend on execution order.
- Module-level logger proxies may be cached; the configuration must account for logger creation before the fixture runs.
- Processor choices may change the rendered message stored in `record.message`, even when the event is captured successfully.
- I still need to confirm whether restoring the saved configuration or calling `structlog.reset_defaults()` provides better isolation with the project's installed structlog version.
- If the full unit suite contains tests that expect stdout rendering, routing all test logs through stdlib logging could expose additional assumptions.

### Edge cases

- Loggers imported before test configuration is applied.
- Multiple tests using `caplog` at different log levels.
- Structured events containing keyword fields, exceptions, or non-string values.
- Repeated test runs in the same Python process and tests executed in different orders.
- Cleanup after a failing test so test-only logging configuration does not leak into later tests.
