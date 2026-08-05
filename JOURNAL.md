## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Structlog is not configured to propgate into the stdlib logging system in tests. Each test fails when asserting on caplog, even though the code itself runs fine.
The test_batch_processor.py unit test is currently broken. A fix would include configuring the structlog so caplog-based assertions work and these tests pass.

**Branch name:** bug/159-structlog-output-not-captured-by-pytest-caplog

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Failing test:** `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`

**Steps to reproduce:**
1. From the repo root, run the batch processor unit tests:
   ```
   python -m pytest tests/unit/test_batch_processor.py -v
   ```
2. Observe the result: `1 failed, 10 passed`.

**Reproduction summary:**
`test_empty_chunks_list_returns_empty` fails with `AssertionError: assert ('Empty chunks list' in '' or False)` — `caplog.text` is empty and `caplog.records` is empty. The captured stdout shows the warning *was* emitted (`[warning  ] Empty chunks list provided to BatchEmbeddingProcessor`), but structlog uses its default configuration (`structlog.get_logger()` in `batch_processor.py:7`) which prints straight to stdout instead of propagating through Python's stdlib `logging`. Since pytest's `caplog` fixture only captures stdlib `logging` output, the log record never reaches `caplog`, so the assertion fails even though the code runs correctly.

**PLAN.md link:** https://github.com/Nexus-00/pathreview/blob/bug/159-structlog-output-not-captured-by-pytest-caplog/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
1. The autouse configure_structlog_for_tests fixture in tests/conftest.py configures structlog with stdlib.LoggerFactory(), cache_logger_on_first_use=False, and a plain ConsoleRenderer(colors=False).

2. The fixture sets the root logger to DEBUG so WARNING-level records propagate to caplog's handler. I verified via the target test, which asserts on both caplog.text and caplog.records[*].message — both are populated, and it passes.

**Next steps:**
Implementing the rest of the plan, through steps 3 to 5: Run the target test, run the full suite, commit, then submit the PR.

**Blockers:**
Time management is an issue. I've been busy throughout the entire week, and did not make as much progress as I wanted to in the middle of the week.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/672

**Branch:** bug/159-structlog-output-not-captured-by-pytest-caplog

**What you built:**
Added an autouse fixture in `tests/conftest.py` that reconfigures structlog to route events through Python's stdlib `logging` (via `structlog.stdlib.LoggerFactory()` with `cache_logger_on_first_use=False` and a plain, non-ANSI `ConsoleRenderer(colors=False)`) and raises the root logger to `DEBUG` so WARNING records reach pytest's caplog handler. Because structlog config is process-global, every module using `structlog.get_logger()` now has its logs captured by caplog during tests, and the fixture calls `structlog.reset_defaults()` on teardown to avoid config bleed.

**Tests added or updated:**
`tests/conftest.py` — added the `configure_structlog_for_tests` autouse fixture; no test assertions were changed. This unblocks the existing failing test `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty` (which asserts on both `caplog.text` and `caplog.records`) and enables caplog-based assertions suite-wide.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
- `make test-unit`: the fix takes the unit suite from 53 failing to 52 (fixes the target test, zero new failures). The remaining 52 failures are pre-existing and unrelated to #159 (async-mock setup and domain-logic issues in `review_service`, `resume_parser`, `tech_detector`, etc.).
- `make check`: `tests/conftest.py` is clean under `ruff` and `black`; `mypy`'s `typecheck` target does not cover `tests/`. The 182 `make check` errors are all pre-existing and outside the scope of this issue.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in for my Pull Request.

**How you responded:**
I did not receive feedback.

---

### Reflection

**What was harder than you expected?**
What was harder than I expected was the workflow process of finding the offending part of the codebase, then ensuring that I understood why it was a problem in the issue on GitHub, before then having to understand how to implement a fix in the way that meets Contributor standards.

**What did you learn about working in a large codebase?**
When I'm building my own project, I know what I want, and I am free to implement changes as I see fit, I have an easier time remembering which parts of the codebase correspond to which module, I am familiar with libraries that I use, and I don't have to wait for pull requests to make progress in the project.

When contributing to someone else's production code, I have very limited insight of the codebase. I feel like that unless I use the project frequently in my day-to-day work, I don't have as much of an incentive or project-wide knowledge to make meaningful contributions to someone else's codebase. ALso having to follow their conventions is expected, but I think community code contributions have multiple layers of friction: making the right changes, following conventions, understanding the relevant parts of the codebase, determining if it is even worth contributing, etc.

**How did AI tools help — and where did they fall short?**
For this module, AI assistance was the most useful in gaining the understanding of the codebase. I understood what test_batch_processor.py was meant to do, and I was able to make targeted changes that fixed a bug and made one more test pass. For my intervention, I still needed to direct Claude Code to make sure contributor guidelines were met, and I ran the tests myself.

**What would you do differently if you started over?**
One thing that I would do differently, is picking a different, more difficult issue that doesn't involve the test case itself, but rather some implementation that has a test case. I feel like with so many different issues to take on for Pathreview, it's hard to say that seeing test cases would be useful if I only expect a few of them to fail, not many of them at once.

**What are you most proud of from this module?**
I'm most proud of practicing on making my first pull request on a somewhat real codebase. With the current hiring environment, I'm not too sure if hiring managers or recruiters pay attention to contributions made on GitHub, or work past the resume. With AI being able to fill out resumes and submit them, I'm not too sure if credentials on my Resume or contributions on GitHub would matter as much as before AI.