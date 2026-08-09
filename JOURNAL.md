## Week 7: Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses structlog for application logging, but its test configuration does
not send those events through Python's standard logging system. As a result,
tests that use pytest's `caplog` fixture cannot inspect log output even when the
application correctly emits it. The affected test currently prints the expected
warning to stdout, then fails because `caplog` is empty. A successful fix will
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

## Week 8: Reproduction and solution planning

**Reproduction commit link:** [0bdd676](https://github.com/nancypatel12/pathreview/commit/0bdd67696f461d28d00f9733c637de8cda5e053d)

**Reproduction summary:**
Running `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty` printed the warning to stdout, but produced zero `caplog` records. The reproduction test now requires a warning `LogRecord` with the expected message, which failed before the test logging configuration was added.

**PLAN.md link:** [PLAN.md](https://github.com/nancypatel12/pathreview/blob/test/159-structlog-caplog-capture/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
The full unit suite has unrelated baseline failures, including unavailable tokenizer downloads and failures in review, parser, and detector tests. The focused batch-processor suite passes after the logging configuration change.

## Week 9: Solution building and PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed the planned test-environment fix. The shared pytest configuration now routes structlog events through Python's standard logging system, and the batch-processor regression test verifies the warning through `caplog`. I also added the `PLAN.md` implementation details and documented the known unrelated suite failures.

**Next steps:**
I planned to run the focused test and the broader checks, review the diff for scope and style, then submit the pull request with the test results and pre-existing failures clearly identified.

**Blockers:**
The focused test passes, but the full unit suite still has unrelated failures caused by existing review, parser, detector, and tokenizer-download issues.

### Check-in 2 (end of week)

**PR link:** Submitted from the `test/159-structlog-caplog-capture` branch for issue #159.

**Branch:** `test/159-structlog-caplog-capture`

**What you built:**
I added a session-scoped pytest fixture that configures structlog with `LoggerFactory`, `BoundLogger`, and `render_to_log_kwargs`, allowing events to become standard-library log records that pytest can capture. The fixture disables logger caching during tests and resets structlog during teardown so the test configuration does not leak into other runs.

**Tests added or updated:**
`tests/unit/test_batch_processor.py` now asserts the expected warning through `caplog`, and `tests/conftest.py` contains the shared test logging configuration. The focused batch-processor test passes after the fix. The full unit suite continues to report unrelated baseline failures, which were documented rather than treated as logging regressions.

**Self-review confirmation:** [ ] `make check` passes  [ ] `make test-unit` passes, with unrelated pre-existing failures documented above

**Draft PR feedback received from:** none

## Week 10: Iteration and reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in during this module. Per the Summer 2026 course note, reviewer feedback is not provided for this assignment.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was tracing why a warning that visibly appeared during pytest was still missing from `caplog`. The application used structlog, while the test expected Python logging records, so the output path looked correct from the terminal but was not connected to the fixture. I also had to separate the logging problem from unrelated full-suite failures, including tokenizer downloads and failures in other modules, instead of assuming every failure came from my change.

**What did you learn about working in a large codebase?**
A small issue can cross several boundaries even when the final code change is local. I had to inspect the failing test, the batch processor, shared pytest setup, and the production logging configuration before choosing the right integration point. In someone else's codebase, preserving existing application behavior matters as much as making the test pass, so I kept the production logging calls unchanged and limited the configuration change to the test environment.

**How did AI tools help, and where did they fall short?**
AI tools helped me locate the relevant logging and pytest files, explain the structlog-to-standard-logging pipeline, and organize the solution into concrete steps in `PLAN.md`. They were useful for generating possible configuration patterns and identifying edge cases such as logger caching and global configuration state. They could not replace running the tests or deciding which failures were genuinely related, and I still had to verify the suggested code against this repository's existing fixtures and behavior.

**What would you do differently if you started over?**
I would establish the baseline results for both `make check` and `make test-unit` earlier and record them before changing the reproduction test. That would make the final comparison clearer. I would also confirm the exact pull-request and branch state earlier, because two similarly named branches can make it unclear which `/tree/<branch>` URL the grader should open.

**What are you most proud of from this module?**
I am most proud of turning a confusing test symptom into a focused, maintainable regression test. The fix does not alter the application's logging calls or production behavior. It makes the test environment accurately represent the logging interface that `caplog` is designed to inspect, while also handling teardown and logger caching explicitly.
