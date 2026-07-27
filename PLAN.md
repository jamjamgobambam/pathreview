## Solution plan

**Issue:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

### Understand

`BatchEmbeddingProcessor.process([])` emits its warning through structlog, but
the test process never configures structlog to use Python's standard logging
pipeline. Structlog therefore uses its default print logger, which writes the
event to stdout. Pytest displays that output but `caplog.records` remains empty.
The expected behavior is for a structlog warning to create a standard-library
`LogRecord` that `caplog` can inspect, without changing application log calls.

### Map

- `tests/conftest.py`: shared pytest setup and the appropriate location for a
  session-wide structlog configuration.
- `tests/unit/test_batch_processor.py`: the regression test that exercises the
  empty-chunk warning and verifies the captured record.
- `ingestion/embeddings/batch_processor.py`: emits the warning being tested;
  no behavior change is expected in this module.
- `core/logging.py`: production and development logging configuration. It is a
  reference point for maintaining compatible processors, but is not required
  for the test-only setup.

### Plan

1. Make the existing batch-processor assertion require one warning record,
   rather than accepting stdout output, to demonstrate the missing capture.
2. Add a session-scoped autouse fixture in `tests/conftest.py` that configures
   structlog with `structlog.stdlib.LoggerFactory`, `BoundLogger`, and
   `render_to_log_kwargs` so events reach standard logging.
3. Disable logger caching for the test configuration and reset structlog after
   the session so loggers created in one test run cannot retain stale settings.
4. Run the focused batch-processor suite, then the full unit suite to identify
   regressions separately from existing failures.

### Inputs & outputs

The fixture receives structlog event dictionaries, including the event message,
log level, and any contextual fields supplied by application code. It produces
standard-library log records. Tests using `caplog` should be able to assert the
record level and message while contextual fields remain available as logging
extras.

### Risks & unknowns

- Structlog configuration is global. A session fixture must restore defaults so
  it does not leak into another pytest invocation in the same interpreter.
- Logger caching can preserve a logger created before the test fixture runs;
  test configuration must avoid that cache.
- The full unit suite currently has unrelated failures, including unavailable
  tokenizer downloads and assertions in other modules. Those failures must not
  be mistaken for a logging regression.

### Edge cases

- Warnings emitted before an individual test calls `caplog.set_level` should
  still follow the standard logging path.
- Events with structured fields, exceptions, and non-string values must not
  prevent record creation.
- Loggers imported before fixture execution must use the configured factory
  when first invoked.
- The fixture teardown must leave structlog in its default state.
