# PLAN.md

---

Solution Plan: Fix Structlog Capture in Pytest
Issue: https://github.com/ascherj/pathreview/issues/159

## Understand
The pytest test test_empty_chunks_list_returns_empty in tests/unit/test_batch_processor.py is failing because of a logging integration mismatch:

The Root Cause: Pytest's built-in caplog fixture captures standard Python logging library records. However, the code under test (ingested/embeddings/batch_processor.py) utilizes structlog.

The Disconnect: Standard caplog cannot natively inspect structlog output unless structlog is explicitly configured to processor-chain into the standard library logging framework.

## Map
Modules/Files Affected:

ingested/embeddings/batch_processor.py (Target implementation)

tests/unit/test_batch_processor.py (Test file)

tests/unit/conftest.py (Optional: Test configuration/fixtures)

Specific Components:

The caplog fixture parameter in test_empty_chunks_list_returns_empty.

structlog configuration settings within the test environment.

## Plan
Configure Structlog for Testing: Update the test configuration (conftest.py or directly inside the test setup) to ensure structlog outputs via standard library logging handlers so caplog can intercept them.

Refactor the Test: Adjust test_empty_chunks_list_returns_empty in tests/unit/test_batch_processor.py to properly assert against the captured structured log output.

Verify Locally: Run pytest tests/unit/test_batch_processor.py to confirm the test passes and no regressions are introduced elsewhere in the suite.

## Inputs & Outputs
Input: An empty chunks list passed to the batch processor function.

Output: A structured log message indicating an empty list was processed, successfully intercepted and validated by the test framework.

## Risks & Unknowns
Risk: Modifying global structlog configurations during tests might leak state and affect subsequent test cases.

Mitigation: Use local fixtures with cleanup/teardown logic (e.g., reset_defaults) to isolate structlog configuration changes to the specific test module.

## Edge Cases
Differences in log formatting between structured key-value dictionaries and standard string messages during assertion matching.