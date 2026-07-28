## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1

**Problem summary:**
The app logs using structlog, but structlog isn't configured to route its output into Python's standard logging module during tests. Since pytest's caplog fixture only captures logs going through stdlib logging, any test asserting on caplog fails even when the expected log event genuinely fires. For example, test_empty_chunks_list_returns_empty in tests/unit/test_batch_processor.py fails on its caplog assertion even though the warning is visibly printed to stderr. I confirmed this by reading tests/conftest.py, which currently has no logging or structlog setup at all, just two unrelated fixtures. The fix is to configure structlog in conftest.py (likely via structlog.stdlib processors or structlog.testing.capture_logs) so its output propagates into stdlib logging and becomes visible to caplog. This affects the test suite broadly, since any test relying on caplog to check log output is currently unreliable, not just the one in test_batch_processor.py.

**Branch name:** fix/159-structlog-caplog-capture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Checklist reasoning:**

- **Understanding the issue:** I can explain this without re-reading it,structlog logs
aren't wired into stdlib logging during tests, so pytest's `caplog` fixture (which only
  hooks into stdlib logging) can't see log events that structlog actually emits. I confirmed
  this by reading `tests/conftest.py`, which has no logging/structlog setup at all, and by
  reading the failing test (`test_empty_chunks_list_returns_empty` in
  `tests/unit/test_batch_processor.py`), which asserts on `caplog.text`/`caplog.records`.
- **Tier fit:** This is my first open source contribution, so Tier 1 is the right level.
  The fix is scoped to one file (`conftest.py`) and doesn't require understanding the
  broader system.
- **Codebase readiness:** I located and read both `conftest.py` and the test file end-to-end
  before claiming the issue, and I have a rough plan (configure structlog via
  `structlog.stdlib` processors or `capture_logs` so logs propagate to stdlib logging).
- **Scope and crowding:** I checked the issue comments. At the time I claimed it, #159 had
  fewer claims than issues like #154/#155, and no PR was linked yet, so I expect smoother
  coaching/review. I estimate this is a 3–6 hour Tier 1 fix, achievable well within the
  Week 8–9 window, with no blockers noted on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/turanyavarri/pathreview/commit/fedded9

**Reproduction summary:**
Ran `pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -v` and confirmed the failure: `caplog.text` was empty even though the captured stdout showed the log line `[warning] Empty chunks list provided to BatchEmbeddingProcessor` was actually emitted. This confirms structlog output isn't propagating into stdlib logging, so caplog can't see it.

**PLAN.md link:** https://github.com/turanyavarri/pathreview/blob/fix/159-structlog-caplog-capture/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
Still need to check how structlog is configured in the app's production code (likely somewhere in `core/`) to make sure the test fixture mirrors the real processor chain rather than reinventing it.