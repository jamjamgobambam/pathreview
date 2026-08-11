## Solution plan

**Issue:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause appears to be that structlog is configured to emit through its own processors and standard library logging handlers, but pytest's caplog fixture is not receiving those events in tests. The expected behavior is that log messages emitted during unit tests should appear in caplog so assertions like the one in the batch processor tests can pass. The actual behavior is that the warning is emitted to stdout instead of being captured by pytest's log records.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- [core/logging.py](core/logging.py) — logging setup for structlog and stdlib logging
- [tests/unit/test_batch_processor.py](tests/unit/test_batch_processor.py) — existing reproduction of the caplog failure
- [ingestion/embeddings/batch_processor.py](ingestion/embeddings/batch_processor.py) — module that emits the warning being asserted in tests

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Inspect the current structlog configuration and confirm how it interacts with pytest's log capture.
2. Adjust logging configuration so structlog messages are routed into the standard logging pipeline that caplog observes during tests.
3. Add or keep a focused regression test that proves log output is visible to caplog.
4. Run the relevant test suite to verify the fix and ensure no regressions in logging behavior.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input: log events emitted by modules using structlog during test execution.

Output: those log events should be visible through pytest's caplog fixture and should be captured in test assertions without relying on stdout output.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- Changing the logging pipeline could alter application logging format or behavior outside tests.
- The project may have other test files or modules that depend on a specific logging setup, so the fix should stay minimal and backward-compatible.
- The exact structlog/pytest interaction may depend on how logging is initialized during test startup.

### Edge cases
What inputs or states should your fix handle gracefully?

- Empty or missing log messages
- Tests that run without explicit logging configuration
- Different log levels such as warning, info, and error
- Situations where logging is initialized multiple times during the test session
