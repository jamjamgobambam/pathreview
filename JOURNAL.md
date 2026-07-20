## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1

**Problem summary:**
The app logs using structlog, but structlog isn't configured to route its output into Python's standard logging module during tests. Since pytest's caplog fixture only captures logs going through stdlib logging, any test asserting on caplog fails even when the expected log event genuinely fires. For example, test_empty_chunks_list_returns_empty in tests/unit/test_batch_processor.py fails on its caplog assertion even though the warning is visibly printed to stderr. I confirmed this by reading tests/conftest.py, which currently has no logging or structlog setup at all, just two unrelated fixtures. The fix is to configure structlog in conftest.py (likely via structlog.stdlib processors or structlog.testing.capture_logs) so its output propagates into stdlib logging and becomes visible to caplog. This affects the test suite broadly, since any test relying on caplog to check log output is currently unreliable, not just the one in test_batch_processor.py.

**Branch name:** fix/159-structlog-caplog-capture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger