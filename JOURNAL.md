## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses structlog for application logging, but its test configuration does
not send those events through Python's standard logging system. As a result,
tests that use pytest's `caplog` fixture cannot inspect log output even when the
application correctly emits it. The affected test currently prints the expected
warning to stderr, then fails because `caplog` is empty. A successful fix will
configure structlog for the test environment so caplog-based assertions receive
and can verify the emitted events.

**Selection notes:**
This is a focused Tier 1 test-infrastructure bug with a clear, local
reproduction command and a defined expected result. It is limited to the
logging/test configuration rather than broad application behavior, so it is
appropriate to implement and verify with targeted regression tests. The issue
is open, unassigned, and has no linked branch or pull request.

**Branch name:** test/159-structlog-caplog-capture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [0bdd676](https://github.com/nancypatel12/pathreview/commit/0bdd67696f461d28d00f9733c637de8cda5e053d)

**Reproduction summary:**
Running `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty` printed the warning to stdout, but produced zero `caplog` records. The reproduction test now requires a warning `LogRecord` with the expected message, which failed before the test logging configuration was added.

**PLAN.md link:** [PLAN.md](https://github.com/nancypatel12/pathreview/blob/test/159-structlog-caplog-capture/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
The full unit suite has unrelated baseline failures, including unavailable tokenizer downloads and failures in review, parser, and detector tests. The focused batch-processor suite passes after the logging configuration change.
