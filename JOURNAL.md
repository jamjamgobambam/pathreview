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

**Reproduction commit link:** https://github.com/harshi-puli/pathreview/tree/fix/159-stucture-output-capturing

**Reproduction summary:**
I ran `.venv/bin/python -m pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q` and confirmed the failure. The captured stdout showed the expected warning log line was actually emitted, but `caplog.text` and `caplog.records` were empty, proving structlog's output never routes through Python's stdlib logging module that `caplog` reads from.

**PLAN.md link:** https://github.com/harshi-puli/pathreview/blob/fix/159-stucture-output-capturing/PLAN.md

**Walkthrough video (recommended):** no video.

**Blockers or open questions:**
Nothing so far.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 1: added an autouse `configure_structlog_for_tests` fixture to tests/conftest.py that configures structlog with `structlog.stdlib.LoggerFactory()` and `structlog.stdlib.BoundLogger`, ending the processor chain in `ProcessorFormatter.wrap_for_formatter`. Verified `test_empty_chunks_list_returns_empty` now passes, and diffed the full suite's failures before/after the change to confirm no regressions.

**Next steps:**
Open the PR and address review feedback. Still need to reconcile the self-review checklist, since the repo has pre-existing, unrelated lint errors and unit test failures that make `make check` / `make test-unit` fail suite-wide regardless of this fix.

**Blockers:**
None specific to this fix. The repo already has ~52 failing unit tests and ~182 lint errors unrelated to structlog/caplog (confirmed present on the branch before my change too), so `make check` / `make test-unit` can't be checked as fully green for the whole suite.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/932)

**Branch:** fix/159-stucture-output-capturing

**What you built:**
An autouse pytest fixture in tests/conftest.py that configures structlog to route through stdlib logging (`LoggerFactory` + `BoundLogger` + `ProcessorFormatter.wrap_for_formatter`) instead of structlog's default `PrintLogger`, which printed straight to stdout and bypassed the `logging` module entirely. This lets `caplog`-based assertions see structlog-emitted log events.

**Tests added or updated:**
No test files were changed — only tests/conftest.py. The existing repro case, `tests/unit/test_batch_processor.py::test_empty_chunks_list_returns_empty`, now passes unmodified with the new fixture in place.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes — "passes" here means no new failures introduced, per the documented pre-existing baseline below.

**Pre-existing failures (documented):**
Ran `make check` and `make test-unit` on `main` before making any changes, then again after, and diffed the results:
- `make test-unit` — before: 53 failed, 375 passed. After: 52 failed, 376 passed. Diffing the failing test names shows exactly one line removed (`test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`, the issue's repro case) and zero other changes in either direction.
- `make check` — before: 182 lint errors (fails at the `lint` step, same set of pre-existing ruff findings unrelated to structlog/logging). After: 182 lint errors, byte-identical rule-code lines (confirmed via diff — 161 matching lines, 0 differences).
- Conclusion: this change fixes the target test and introduces zero new lint or test failures; the pre-existing 52 test failures and 182 lint errors are unrelated to structlog/caplog and out of scope for this issue.

**Draft PR feedback received from:** TF

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review or comments on PR #932 yet (confirmed via `gh pr view 932` — reviews and comments are both empty as of this writing). TF gave informal feedback pre-PR, but hadn't left anything on the PR itself by the time I checked.

**How you responded:**
N/A yet — nothing to respond to. Will update this section once a review comes in.

---

### Reflection

**What was harder than you expected?**
Confirming the fix was actually correct took more work than writing it. The repo already had 52 failing unit tests and 182 lint errors unrelated to this issue, so a naive "did the suite pass?" check would've been meaningless either way. I had to stash my change, capture a clean before/after run of `make test-unit` and `make check`, and diff the exact failure lists to prove my fix changed exactly one thing and nothing else. That habit — always get a before/after diff, not just a pass/fail — was the biggest process lesson.

**What did you learn about working in a large codebase?**
In your own project, a green test suite is a reasonable bar. In someone else's production codebase, "no new failures" is the actual bar, and you have to go prove that explicitly — you can't just point at `make check` failing and assume it's your fault, but you also can't wave it away without evidence. I also learned to trace a bug to its root cause before touching anything: the real issue wasn't in the test file at all, it was that `configure_logging()` in `core/logging.py` was never being called during tests, so structlog silently fell back to a default that bypassed `logging` entirely.

**How did AI tools help — and where did they fall short?**
AI was most useful for the mechanical-but-tedious parts: reproducing the failure, tracing why `caplog` came up empty while stdout clearly showed the log line, and running the before/after diffs across two commands instead of eyeballing long test output. It also caught something I would've missed — the `mypy` pre-commit hook failing on a missing return type annotation on the fixture — and fixed it in one pass. Where it fell short was anything requiring my own judgment or memory: it couldn't tell me what TF's actual feedback was, or make the call about whether "82 pre-existing lint errors" was an acceptable baseline to build on top of — that's a decision I had to own.

**What would you do differently if you started over?**
I'd run the before/after `make check` / `make test-unit` baseline *before* writing any fix, not after — I ended up doing it retroactively to document pre-existing failures, but capturing it up front would have saved a step and given me a cleaner paper trail from the start.

**What are you most proud of from this module?**
Not the fix itself (it's a small, four-line fixture) — I'm proud of the rigor around it: diffing exact failure sets instead of trusting a pass/fail count, and being able to say with evidence, not just confidence, that the change doesn't make anything worse.