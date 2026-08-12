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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/parker-cassar/pathreview/commit/bd2dec64128583ee3d5e8a44daa9cf483f427758

**Reproduction summary:**
I ran:
`.venv/bin/pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -v`

Result: FAILED. stdout showed the warning (`Empty chunks list provided to BatchEmbeddingProcessor`), but `caplog.text` was `''`, so the assertion on caplog failed. That matches the issue: structlog prints the event, pytest caplog never sees it. `tests/conftest.py` has no structlog/stdlib wiring today. The log call lives in `ingestion/embeddings/batch_processor.py` (`logger.warning(...)`).

**PLAN.md link:** https://github.com/parker-cassar/pathreview/blob/fix/159-structlog-caplog/PLAN.md

**Loom / walkthrough:** [ ] Recorded or scheduled (still need to record the ~2 min reproduce + plan Loom)

**Blockers or open questions:**
- None blocking Week 8. Open question for implementation: whether a small test-only structlog config in `conftest.py` is enough, or whether reusing `core.logging.configure_logging()` also feeds caplog cleanly. Plan is to try test-specific stdlib setup first.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the test-only structlog config from PLAN.md in `tests/conftest.py` (stdlib `LoggerFactory`, BoundLogger wrapper, ConsoleRenderer handoff). Confirmed the repro test `test_empty_chunks_list_returns_empty` passes with the warning visible in `caplog`. Added `tests/unit/test_structlog_caplog.py` for warning/info capture. Left production `core/logging.py` unchanged.

**Next steps:**
Run full `make check` / `make test-unit`, document pre-existing failures, open the PR against `ascherj/pathreview`, and finish Check-in 2 with the PR link.

**Blockers:**
Pre-existing suite-wide lint/typecheck/unit failures on main; confirming our diff does not add new ones.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1029

**Branch:** `fix/159-structlog-caplog`

**What you built:**
Configured structlog in the test suite so events go through stdlib logging and pytest's `caplog` can see them. That fixes empty `caplog.text` for app warnings (including the empty-chunks case) without changing production logging.

**Tests added or updated:**
- `tests/unit/test_structlog_caplog.py` — warning and info events appear in `caplog`
- Existing `tests/unit/test_batch_processor.py::test_empty_chunks_list_returns_empty` now passes (was the reported failure)

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Note: full-repo `make check` / `make test-unit` still fail for pre-existing unrelated issues (~182 ruff, ~103 mypy, ~52 unit failures). Before this change: 55 failed / 375 passed. After: 52 failed / 378 passed. Changed files pass ruff/black/mypy via pre-commit; no new failures introduced.

**Draft PR feedback received from:** none

## Week 10: Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No feedback

**Summary of feedback:**
No feedback came in. [PR #1029](https://github.com/ascherj/pathreview/pull/1029) against `ascherj/pathreview` is still open with no maintainer or reviewer comments. Per the Summer 2026 note, reviewer feedback is not a feature this term, so I did not expect a maintainer response and none arrived by the end of the week.

**How you responded:**
No changes were warranted since there was nothing to respond to. I re-verified the branch is clean and the PR still reflects the intended diff (test-only structlog wiring in `tests/conftest.py`, plus `tests/unit/test_structlog_caplog.py`), so it stays merge-ready if a reviewer does pick it up later.

---

### Reflection

**What was harder than you expected?**
The actual "fix" was small, but making structlog and pytest's `caplog` cooperate was fiddlier than I assumed. `caplog` only ever sees stdlib `logging`, so the fix wasn't "call a function." It meant understanding structlog's processor pipeline well enough to route events through a stdlib `LoggerFactory`/`BoundLogger` in the test config without changing how the app logs in production. The other genuinely hard part was epistemic, not technical: the suite was already badly red on `main` (~55 failed before I touched anything), so proving my change was clean meant carefully baselining before and after (55 failed, then 52 failed) instead of just eyeballing a green run.

**What did you learn about working in a large codebase?**
The biggest shift from my own projects is that "does it pass?" is the wrong question. "Did I make it *worse*?" is the right one. On a repo with a pre-existing wall of ruff/mypy/unit failures, I had to isolate my diff's impact rather than trust a global `make check`. I also learned to respect boundaries I didn't set: the temptation was to "fix" production logging in `core/logging.py`, but the correct, reviewable move was to keep the change test-only in `conftest.py` and leave production behavior untouched. Contributing to someone else's code is mostly restraint and evidence, not cleverness.

**How did AI tools help, and where did they fall short?**
AI was most useful for orienting fast: explaining structlog's processor chain, sketching the initial `conftest.py` config, and helping me phrase the journal/PR write-ups precisely. Where it fell short was the exact runtime interaction between structlog's `LoggerFactory` and the handler pytest's `caplog` installs. Suggested configs looked plausible but didn't actually surface events in `caplog.text` until I ran the repro test repeatedly and adjusted. That loop (run `pytest ...::test_empty_chunks_list_returns_empty -v`, inspect, tweak) was something I had to own; AI could describe the pieces but couldn't confirm they worked in this specific suite.

**What would you do differently if you started over?**
I'd pick an issue with fewer competing claimants. #159 had others eyeing it, which added pressure even though there was no open PR. I'd also baseline the full test suite on `main` on day one so I had the before and after failure counts ready from the start, instead of reconstructing them near submission. And I'd record the Week 8 walkthrough Loom when I first reproduced the bug, while the context was fresh, rather than leaving it as an open to-do.

**What are you most proud of from this module?**
Keeping the fix disciplined: a real bug (app warnings invisible to `caplog`) resolved with a minimal, test-only change and zero new failures introduced, backed by concrete before and after numbers rather than a vague "it works." In a codebase that was already noisy and red, shipping a change I could defend line-by-line felt more valuable than the size of the diff.
