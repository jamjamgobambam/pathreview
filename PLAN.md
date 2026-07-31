# Issue #159 Solution Plan

## Issue Summary

PathReview uses Structlog for application logging, but the pytest configuration does not route Structlog events through Python’s standard logging system.

As a result, tests that use pytest’s `caplog` fixture cannot find expected log records. The application emits the expected event, but the output is printed to the captured console stream instead of being stored in `caplog.text` or `caplog.records`.

GitHub issue: [Issue #159 — structlog output is not captured by pytest caplog](https://github.com/ascherj/pathreview/issues/159)

## Reproduction

I reproduced the failure with:

```bash
pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q
```

Before the fix, the test failed because:

- The expected warning was visibly emitted by Structlog.
- `caplog.text` remained empty.
- `caplog.records` did not contain the expected log record.
- The application behavior was correct, but pytest could not capture the event through the standard logging system.

Reproduction commit: [580d766](https://github.com/rodmendoza2404/pathreview/commit/580d7661565a7cf8d0f2c3ec2d86679b14a81db4)

## Root Cause

Pytest’s `caplog` fixture captures `logging.LogRecord` objects emitted through Python’s standard-library logging system.

The existing Structlog test configuration rendered log events directly to its configured output stream. Because those events did not pass through the standard logging pipeline, pytest could display the output but could not expose it through `caplog.text` or `caplog.records`.

This was a logging-configuration problem rather than a missing application log statement.

## Proposed Solution

Configure Structlog specifically for the pytest environment in `tests/conftest.py`.

The test configuration should:

1. Route Structlog events through `structlog.stdlib`.
2. Preserve event messages and logging levels.
3. Allow pytest’s `caplog` fixture to capture the resulting standard-library log records.
4. Avoid changing the application’s production logging configuration.
5. Avoid duplicate log output.
6. Avoid leaking unexpected logging state between tests.

## Files to Change

### `tests/conftest.py`

Add the pytest-specific Structlog configuration required for standard-library logging and `caplog` compatibility.

### Documentation files

- `PLAN.md` documents the analysis and intended solution.
- `JOURNAL.md` documents reproduction, implementation, testing, and relevant links.

No production application modules should need modification.

## Implementation Steps

1. Reproduce the failing batch-processor test.
2. Confirm that Structlog emits the expected event while `caplog` remains empty.
3. Review the existing pytest and Structlog configuration.
4. Configure Structlog in `tests/conftest.py` to use the standard-library logging pipeline.
5. Ensure that the log level and event message remain available to `caplog`.
6. Rerun the original reproduction test.
7. Run the complete batch-processor unit-test module.
8. Confirm that no duplicate logging records are produced.
9. Review the Git diff to ensure the implementation remains limited to Issue #159.
10. Document the implementation and verification results in `JOURNAL.md`.

## Testing Strategy

### Original reproduction test

```bash
pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q
```

Expected result:

- The test passes.
- The expected Structlog warning is available through `caplog`.
- The event is not captured only as console output.

### Focused regression tests

```bash
pytest tests/unit/test_batch_processor.py -q
```

Expected result:

- All 11 batch-processor tests pass.

### Repository checks

Before opening a pull request, the project contribution guide requires:

```bash
make check
make test-unit
```

The repository-wide `make check` currently reports Ruff violations in files outside the Issue #159 changes. Those unrelated files should not be automatically modified as part of this focused issue branch.

## Risks and Edge Cases

- A handler could be added twice and create duplicate records.
- Structlog caching could retain an outdated logger configuration.
- Incorrect processor ordering could remove the event message or log level.
- Global test configuration could affect unrelated tests.
- A solution that only captures console output would not satisfy tests using `caplog`.
- Changing production logging configuration could unnecessarily expand the issue’s scope.

## Out of Scope

The following work is outside Issue #159:

- Rewriting application log statements.
- Replacing `caplog` assertions with stdout or stderr assertions.
- Redesigning production logging.
- Fixing repository-wide Ruff violations in unrelated files.
- Refactoring unrelated unit tests.
- Changing application behavior outside the test logging configuration.

## Success Criteria

The solution is successful when:

- The original reproduction test passes.
- Structlog events are captured by `caplog`.
- The event message and logging level remain available.
- All 11 tests in `tests/unit/test_batch_processor.py` pass.
- Logs are not duplicated.
- Production application files remain unchanged.
- The branch contains only Issue #159 implementation and documentation changes.

## Process Note

This planning document was committed after implementation commit `a7a8fc6` because it was accidentally omitted during the Week 8 workflow.

The Git history has not been rewritten. This document transparently records the reproduced failure, root-cause analysis, solution design, testing strategy, risks, and intended scope.