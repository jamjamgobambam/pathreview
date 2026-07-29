## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [*] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that the app's logging (via structlog) isn't wired up to feed into Python's standard logging module during test runs. Because of that gap, any test using caplog to check for expected log messages fails, even though the code is correctly producing those log events (you can see them printed to stderr, just not captured by caplog) — test_empty_chunks_list_returns_empty in tests/unit/test_batch_processor.py is one example. The fix involves updating tests/conftest.py to properly configure structlog (using something like structlog.stdlib processors or capture_logs) so its output routes through stdlib logging. Once fixed, caplog-based assertions across the test suite should work correctly and reflect the log events actually emitted by the batch processor and other modules.

**Branch name:** fix/159-stucture-output-capturing

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger

**Selection Notes:** The issue checked all the boxes under the is this right for me checklist

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I ran `.venv/bin/python -m pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q` and confirmed the failure. The captured stdout showed the expected warning log line was actually emitted, but `caplog.text` and `caplog.records` were empty, proving structlog's output never routes through Python's stdlib logging module that `caplog` reads from.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** no video.

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]