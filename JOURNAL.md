# PathReview Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The app logs with structlog, but the test suite still relies on pytest's `caplog` fixture, which only sees stdlib logging. Because structlog is not wired into that path in `tests/conftest.py`, warnings and other events show up on stderr but never land in `caplog.text` / `caplog.records`. That breaks assertions like the empty-chunks warning check in `tests/unit/test_batch_processor.py`, and the same gap can fail any other caplog-based test. A successful fix configures structlog for tests (stdlib processors or `capture_logs`) so those assertions pass without changing production logging behavior.

**Branch name:** fix/159-structlog-caplog

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes ("Is this right for me?"):**
- Scope is small and local: mainly `tests/conftest.py`, maybe a light check that the existing unit test passes. No API, RAG, or frontend changes.
- Repro is clear (`pytest ...::test_empty_chunks_list_returns_empty`), so I can confirm the bug before and after.
- Fits Tier 1: first contribution to this codebase, about a day of reading + a focused fix.
- Skills match: Python testing and logging config, not a full feature build.
- Risk: other people also claimed #159. I am still taking it because there is no open PR yet and the fix is narrow enough to finish cleanly.
- Out of scope for this issue: rewriting how the app logs in production, or converting every test off of `caplog`.
