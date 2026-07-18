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

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
