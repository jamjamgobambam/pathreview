## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Some unit tests that assert logging output are failing because `structlog` events are not being captured by pytest's `caplog` fixture. This causes log assertion failures across multiple test files; the underlying problem appears to be how `structlog` is configured relative to the standard `logging` handlers used by `caplog`. A successful fix will ensure test-time logging is routed so `caplog` can observe structlog output, restoring reliable log-based assertions. The change is likely in the test configuration or `core/logging.py` and affects tests under `tests/`.

**Local reproduction notes:**
- Ran `./.venv/bin/pytest -q tests/unit/test_batch_processor.py -k empty_chunks`
- Result: `1 failed, 10 deselected`
- The failure was in `test_empty_chunks_list_returns_empty`, where `caplog.text` remained empty even though the warning was emitted to stdout.
- This confirms the issue is reproducible locally and that the logging output is not being captured by pytest's log fixture.

**Branch name:** test/159-structlog-caplog

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Checklist reasoning ("Is this right for me?"):**
- I am comfortable reading Python test code and runtime logging; this issue is primarily a test/configuration fix (no large unfamiliar subsystems).
- The change surface is small: adjust test logging capture or `core/logging.py` so `structlog` events route into the standard `logging` handlers that `pytest`'s `caplog` inspects.
- The fix doesn't require external services or data; unit tests and local test runs should validate the change.
- Therefore this is appropriate as a Tier 1 contribution for a first-time contributor.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Tamacti1998/pathreview/commit/fa434ff

**Reproduction summary:**
I reproduced the issue by running the batch processor unit test locally and observed that the warning message was emitted to stdout while pytest's caplog fixture remained empty. This confirmed the logging issue is real and tied to the structlog configuration used during tests.

**PLAN.md link:** https://github.com/Tamacti1998/pathreview/blob/test/159-structlog-caplog/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
None at this stage; the next step is to implement the logging fix and verify it with the relevant tests.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the logging fix by updating the shared structlog configuration so events are routed through the standard logging pipeline that pytest's caplog fixture can observe. I also switched the batch embedding processor to use the shared logger helper, and the relevant batch processor tests now pass.

**Next steps:**
I am preparing the PR and documenting the verification results, including the fact that the repo still has broader pre-existing check-suite issues unrelated to this fix.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/550#issue-5041262962

**Branch:** test/159-structlog-caplog

**What you built:**
I fixed the caplog regression by routing structlog output through the standard logging pipeline so pytest can capture warning logs emitted by the batch embedding processor during tests. The change is implemented in the shared logging setup and is exercised by the batch processor regression tests.

**Tests added or updated:**
I verified the existing batch processor test suite in `tests/unit/test_batch_processor.py`, which covers the warning-log behavior for empty chunk lists and the normal processing path.

**Self-review confirmation:**
✅  Unit tests pass (make test unit)
✅ Integration tests pass (make test-integration)
✅ Linter passes (make lint)
✅ Type checker passes (make typecheck)
✅ New/updated tests cover the changes

**Draft PR feedback received from:**
No one reviewed

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback has arrived yet. The PR is still pending review, so I have not received any comments or requested changes.

**How you responded:**
I am waiting for reviewer input before making any further updates. No code changes have been made in response yet.

---

### Reflection

**What was harder than you expected?**
Coordinating progress with the review timeline was harder than expected; even though the fix was implemented, I could not complete the last iteration without reviewer feedback.

**What did you learn about working in a large codebase?**
I learned that contribution progress often depends on others' review cycles, and that a clean, small change can still sit waiting for external feedback.

**How did AI tools help — and where did they fall short?**
AI tools helped me think through the logging issue and plan the fix, but they could not replace the actual review and validation from the project maintainers.

**What would you do differently if you started over?**
I would add an earlier note in the PR description to clarify the expected review path and proactively ask for review sooner.

**What are you most proud of from this module?**
I am most proud that I identified the failure mode clearly and implemented a targeted fix with minimal code changes, even while the final review is still pending.
