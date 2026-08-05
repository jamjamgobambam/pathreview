## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for core/services/review_service.py is below 40%
 #109

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The review service handles the app's core review process, but most of it isn't tested — coverage is under 40%. To fix this, I'll write unit tests in tests/unit/test_review_service.py that cover the main scenarios: when things work correctly, when part of the process fails, and when it all fails. This will make the service more reliable and easier to maintain.

**Reasoning:**
This is a Tier 2 issue, which fits since I wanted a bit more challenge than a Tier 1 fix. I found review_service.py and tests/unit/test_review_service.py, read through the existing service logic and test structure, and feel confident I understand the main execution paths (success, partial failure, full failure) well enough to write tests without getting stuck. Several other students have also claimed this issue, but since claims are non-exclusive and grading is based on my own work, I'm comfortable with that, and I don't see any blockers. I'm estimating 5-7 hours which fits within the Week 8-9 window.

**Branch name:** test/109-review-service-coverage

**Setup confirmation:** [Yes ] App runs locally at localhost:5173

**Cohort ledger:** [Yes ] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/anuvanuzhat/pathreview/commit/2cc0dc314b7d38680dc0d44744d8c56f77d66db3)

**Reproduction summary:**
I ran this line: pytest --cov=core.services.review_service --cov-report=term-missing tests/unit/test_review_service.py

Result: core/services/review_service.py     135    105    22%   68-79, 98-194, 202-279, 288, 323, 369-390

This shows a 22% coverage.

**PLAN.md link:** https://github.com/anuvanuzhat/pathreview/blob/test/109-review-service-coverage/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The progress I had when completiting for Week 8. A completed Plan.md to figure out what I need to fix.

**Next steps:**
Adding tests for `process_review`'s early-return and failure branches (review not found, profile not found, safety check failure, unhandled exception mid-pipeline), then direct tests for `_run_ingestion_pipeline` and `_run_safety_checks` including the confidence-boundary and multi-source-failure edge cases from the plan, then re-running coverage to confirm it's comfortably above 40%.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/815

**Branch:** test/109-review-service-coverage

**What you built:**
Fixed 13 broken test mocks in `test_review_service.py` (root cause: `AsyncMock` used for synchronous result-object methods) and added new tests covering `process_review`'s success, partial-failure, and full-failure paths plus its helper functions directly. While writing tests for the ingestion pipeline, found and fixed a real bug in `review_service.py`: `IngestedSource` was being constructed with a `raw_data` kwarg that doesn't exist on the model, so every ingestion attempt was silently failing.

**Tests added or updated:**
`tests/unit/test_review_service.py` — fixed the mocking pattern in all 19 original tests; added tests for `process_review`'s happy path (status=complete, sections/overall_score populated), review-not-found and profile-not-found early returns, safety-check failure, and unhandled-exception handling; added direct tests for `_run_ingestion_pipeline` (all sources present, no sources present, one source failing while others succeed, multiple sources failing while one succeeds) and `_run_safety_checks` (missing/empty sections, missing required fields, confidence out of range, and confidence exactly at the 0 and 1 boundaries). Coverage on `core/services/review_service.py` went from 22% to 94%.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: `make check` and `make lint`/`make typecheck` show pre-existing failures unrelated to this change — 6 pre-existing mypy missing-annotation errors and 173 pre-existing ruff lint errors, all in files/lines untouched by this PR, confirmed via `git stash` and scoped `ruff check` on just the two changed files. Documented in full in the PR's Notes for Reviewers.)

**Draft PR feedback received from:** none — ran out of time this week to get a peer review before the deadline



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X ] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
There was an issue that I had to fix that was bigger than what I originally thought would be included with the problem I had picked.
I needed to increase the coverage of my tests above 40% so I assumed writing more tests but I also had to fix a bug within the actual code as well.
The bug wasn't that large it just had to do more so with a small syntax and logic error that prevented some tests from passing but it affected the code
coverage of the review_service file.
This meant that I had to figure out what the failing part of the code was and then write the tests to increase the coverage. It was just more work
than I had anticpated when I originally chose the issue.

**What did you learn about working in a large codebase?**
You have to spend a lot more time familariziing yourself with the code. I used AI a lot to explain certain files to me and how componenets worked together.
When you write your own project from scratch the planning is already kind of done in your head or preplanned. You're more familiar with which files and classes work together. When you are contributing to someone elses code there's a lot that is thrown at you and it is sort of overwhelming. You also have to be more careful in terms of what you are pushing and that's why we have PR. The code is more carefully reviewed and merged when its a large codebase vs your own personal project.

**How did AI tools help — and where did they fall short?**
AI was most useful to explain concepts I didn't understand or when it came to explaining code to me. For example I had a hard time realizing what was wrong with the code coverage until Claude had pointed out why the tests were failing. I used it a lot to summarize methods or tell me what was going on in regards to files and the structure of the code. Honeslty AI didn't really let me down too much for this course. It was able to implement code when I needed and also have it explained to me really well.

**What would you do differently if you started over?**
I chose a tier 2 issue because I thought it would be a good balance. But I chose it in a topic I feel more strongly about which are tests. I don't like writing them but I think that test coverage is an easier topic which I know more about. Im curious to see how I would feel about doing a tier 1 issue for an issue category I'm less confident in. Like for example fixing a bug in the code myself or writing code logic. I think it would have given me more room to grow versus sitcking something I am more comfortable with. 

**What are you most proud of from this module?**
I am most proud of contributing to an open source large database. It was my first taste of what I'll probably mostly be doing in the real world so it was really cool to see what software engineers actually do on a large scale rather than just coding for a class project or a personal project.