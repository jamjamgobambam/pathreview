## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/112)

**Issue title:** Add a performance benchmark for the ingestion pipeline to detect regressions

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
The issue I'm working on is about making the ingestion pipeline fast enough for large portfolio processing without introducing hidden slowdowns. Currently, the codebase lacks an automated performance check to catch regressions at ingestion time, so a slowdown could go unnoticed until it affects users. A successful fix should add a benchmark test that measures a representative ingestions workload and fail if the average runtime exceeds the 30 second threshold. The fix would primary affect the ingestion pipeline and the ingestion and test folders. 

**Branch name:** feature/112-ingestion-performance-benchmark

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Is This Issue Right for Me?**
Part 1 — Understanding the Issue
Can I explain what this issue is asking for in my own words? 
[X] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
I've located the relevant files and confirmed they exist in the codebase.
[X] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
[X] Is the tier a realistic match for where I am right now?

If this is my first open source contribution: I'm choosing Tier 1.
[X] If I've contributed to large codebases before: Tier 2 or 3 is fair game.
[X] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.

[X] I've found and read the specific code the issue references (not just the file — the function or section).
[X] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
[X] I've found the test file for my module and read at least one test end-to-end.

[X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
[X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
[X] This issue has no open blockers or dependencies on other unresolved issues.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AmirFleurizard/pathreview/commit/39a8a8dc1d01a99a2ca5390487b30ede7aabaa0f

**Reproduction summary:**
This is a feature gap, not a bug, so "reproduction" meant confirming the gap rather than triggering an error: `tests/benchmarks/` contains only an empty `__init__.py`, `pytest-benchmark` is listed as a dev dependency in `pyproject.toml` but is never imported anywhere in the codebase, and there is no existing code path (in `ingestion/pipeline.py` or elsewhere) that ingests a full portfolio (resume + multiple repos) in one call — confirming the benchmark test named in the issue genuinely does not exist yet.

**PLAN.md link:** `https://github.com/AmirFleurizard/pathreview/blob/feature/112-ingestion-performance-benchmark/PLAN.md`.

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
- `IngestionPipeline._check_skip` (`ingestion/pipeline.py:280`) queries `db_session` in a way that, if mocked naively (bare `Mock()`), makes every ingestion silently skip — need to make sure the benchmark's mock db session returns `None` from `.first()` so it measures real work, and add a correctness assertion (not just timing) to catch this failing silently in the future.
- Unsure whether this benchmark should be wired into `ci.yml` (it currently only runs `test-unit`/`test-integration`) or stay a local/manual `make test-benchmark` check — benchmark timing tends to be noisy on shared CI runners. Leaning toward local-only for now but want to confirm with @jamjamgobambam before Week 9.
- Want to verify the 30s threshold can actually catch a regression (not just always pass trivially) by temporarily introducing a slowdown locally and confirming the test fails, before considering this done.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Added `tests/benchmarks/test_ingestion_performance.py` and `tests/benchmarks/conftest.py` and committed them on `feature/112-ingestion-performance-benchmark`.
- Created a local `.venv` and installed dev dependencies so linters and `pytest-benchmark` are available.
- Ran a smoke benchmark locally (passed) and ran `make check` / `make test-unit` to capture baseline failures; several pre-existing linter and unit-test failures unrelated to this work were observed and documented.

**Next steps:**
- Iterate on the benchmark harness if needed and verify the test fails when a deliberate slowdown is introduced locally.
- Open a draft PR and request peer/mentor feedback; update the PR with notes about pre-existing failures so graders and reviewers know these are unrelated to this change.
- Add the final (Sunday) check-in and finalize the PR after addressing feedback.

**Blockers:**
- The repository currently has multiple unrelated linter and unit-test failures; these are pre-existing and mean CI may show failures not caused by this benchmark addition.
- Attempted `gh pr create` via CLI failed due to environment/argument limits; I will open the draft PR via the GitHub web UI if needed.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/865

**Branch:** feature/112-ingestion-performance-benchmark

**What you built:**
Added a `pytest-benchmark` test that measures the ingestion pipeline processing a representative portfolio (five repositories plus one resume). The benchmark uses lightweight parser and batch-processor mocks to focus on orchestration overhead and asserts the mean ingestion time across measured runs is <= 30 seconds.

**Tests added or updated:**
- `tests/benchmarks/test_ingestion_performance.py` — benchmark that runs a 5-repo + resume ingestion workload and asserts mean runtime <= 30s.
- `tests/benchmarks/conftest.py` — fixture providing the large portfolio (5 repos + resume) used by the benchmark.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Notes: running `make check` and `make test-unit` before and after these changes revealed multiple pre-existing linter and unit-test failures unrelated to this work. This contribution only adds benchmark tests and fixtures and does not modify production code; it did not introduce new failures locally. See the "Reproduction & solution planning" section above for details and the baseline test outputs.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was turning a feature gap into a reliable benchmark instead of a simple unit test. I had to understand the ingestion pipeline well enough to mock the right components, especially `db_session` and the skip-check logic, so the benchmark measured real work rather than a no-op path.

**What did you learn about working in a large codebase?**
I learned that a large repository often has hidden assumptions and pre-existing failures that affect how you verify a change. It’s important to scope the work cleanly, avoid touching unrelated production code, and document the baseline state clearly so reviewers know what was already broken.

**How did AI tools help — and where did they fall short?**
AI assistance was useful for organizing the benchmark test and summarizing the work in journal form, but it was less helpful for the repository’s specific runtime and CI trade-offs. I still needed to inspect the actual ingestion code and run local experiments to confirm the benchmark behavior.

**What would you do differently if you started over?**
I would validate the benchmark harness earlier with a deliberate slowdown and ask about CI placement up front. That would have made it easier to decide whether this should be a local regression check only or something to integrate more directly into the existing test pipeline.

**What are you most proud of from this module?**
I’m most proud of adding a practical, regression-focused benchmark that targets the ingestion pipeline without changing production logic, and of recording the baseline test state transparently so the contribution is easier to review. It was fun getting to work on a open source project like this and gain semi real world experience.
