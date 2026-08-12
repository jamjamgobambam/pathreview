## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint currently has no test coverage for the case where a user's profile exists but has no ingested documents attached to it. It's unclear whether the endpoint fails gracefully with a proper error response or crashes unexpectedly in this scenario, since nothing exercises that code path today. This affects the API layer, specifically the review-creation flow tested in `tests/unit/test_review_routes.py`. A successful fix will add a test that calls the endpoint under this condition and asserts it returns an appropriate error response rather than an unhandled exception, closing a gap in the test suite around edge-case handling.

**Branch name:** test/88-reviews-no-documents-test

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/Nolawikk/pathreview/commit/b5dc331

**Reproduction summary:**
I traced the bug by reading through `api/routes/reviews.py` and `core/services/review_service.py`. I found that `_run_agent_orchestration` and `_run_rag_retrieval_generation` are placeholder functions that ignore their input entirely, so I wrote a test calling them directly with an empty ingestion results list (simulating a profile with no documents). The test confirmed both functions still return fabricated, non-empty feedback and a normal-looking score, even with zero real input data.

**PLAN.md link:** https://github.com/Nolawikk/pathreview/blob/test/88-reviews-no-documents-test/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Still unsure whether the correct fix is a new "no_data" status or reusing the existing "failed" status - need to check the Review model and how the frontend displays failure states before finalizing the plan.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1-4 from PLAN.md are complete. I added a guard in `process_review` (`core/services/review_service.py`) that checks if `_run_ingestion_pipeline` returns an empty list, and if so, marks the review as `status="failed"` and returns early instead of proceeding to the placeholder agent/RAG functions. I added a new test, `test_process_review_marks_failed_when_no_ingested_sources`, confirming this behavior, alongside the existing reproduction test that documents the original bug. Ran the full test suite (`make test-unit`) and confirmed no new failures: 53 pre-existing failures remain unchanged, and my new test brings the passing count from 376 to 377. Also ran `make check` and confirmed the lint error count is unchanged at 179 (all pre-existing, unrelated to my change).

**Next steps:**
Open a draft PR and request peer/mentor feedback via Slack. Consider sub-task 5 (manual verification through the running app) as a nice-to-have before finalizing.

**Blockers:**
None currently - the fix is implemented and tested. Waiting on peer feedback before finalizing the PR.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/983

**Branch:** test/88-reviews-no-documents-test

**What you built:**
Added a check in `process_review` that detects when a profile has no ingested sources (no GitHub username, portfolio URL, or resume text) and marks the review as `status="failed"` with a logged reason, instead of proceeding to placeholder agent/RAG functions that previously fabricated generic "complete" feedback regardless of input.

**Tests added or updated:**
Added `test_process_review_marks_failed_when_no_ingested_sources` to `tests/unit/test_review_service.py`, verifying the fix. Kept the existing reproduction test documenting the original bug for reference.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** Posted in dts-su26-ai201-program-help-2a Slack channel, awaiting response

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
No reviewer feedback arrived through the PR itself. Per the course note, reviewer feedback isn't a feature in Summer 2026. I did post in the program-help Slack channel asking a peer to review my draft PR (#983) but had not received a response by the end of the module.

**How you responded:**
N/A - no feedback received to respond to.

---

### Reflection

**What was harder than you expected?**
Environment setup took far longer than I expected - getting Docker, Node, and `make` all working correctly on Windows, especially the confusion between PowerShell and Git Bash (commands that worked in one shell silently failed in the other), cost me more time than the actual code fix did. I also didn't expect how much time I'd spend just locating the right files - the issue pointed to `test_review_routes.py`, which didn't even exist in the codebase, so I had to trace the real code path myself through `api/routes/reviews.py` and `core/services/review_service.py` before I understood what was actually broken.

**What did you learn about working in a large codebase?**
The biggest lesson was that the bug wasn't where the issue description implied it would be. The issue title suggested a missing test, but tracing the actual code revealed the real problem was two placeholder functions (`_run_agent_orchestration` and `_run_rag_retrieval_generation`) that silently ignored their input and fabricated output regardless of whether there was real data to analyze. In a codebase I hadn't written, I couldn't assume the surface-level description was the full story - I had to read the call chain end-to-end before I could even reproduce the issue correctly. I also learned to distinguish pre-existing failures from ones I introduced; running `make test-unit` and `make check` before touching anything gave me a baseline (53 failed/376 passed, 179 lint errors) that let me prove my change didn't make anything worse, which mattered a lot for the PR description.

**How did AI tools help - and where did they fall short?**
AI was most useful for tracing logic across multiple files quickly - once I pasted in the route handler and service code, it helped me see the actual data flow (ingestion pipeline returning an empty list, but the downstream functions ignoring that) faster than I would have on my own. It also helped me write mock-based tests that matched the existing test file's conventions. Where it fell short: it initially wrote a test using `AsyncMock()` for the wrong objects, which caused a `'coroutine' object has no attribute 'first'` error - the same failure pattern as a pre-existing, unrelated issue in the codebase (#158). I had to actually understand why that mocking pattern was wrong (AsyncMock makes every child attribute async too) rather than just accepting the first version. AI also couldn't fix filesystem/terminal issues on my machine - things like being in the wrong folder, PowerShell vs. Git Bash PATH differences, or a file with a corrupted name - those all needed direct troubleshooting.

**What would you do differently if you started over?**
I'd check the issue tracker's linked PRs before spending time reasoning about candidate issues - three of my top four choices (#155, #154, #146) already had open PRs, which I only discovered by checking each issue's page individually. I'd also verify my local dev shell (Git Bash vs. PowerShell) once at the very start and stick to it consistently, instead of bouncing between the two and hitting the same PATH problem multiple times across different weeks.

**What are you most proud of from this module?**
Tracing the actual root cause. The issue as written suggested a simple "add a missing test" task, but I found and proved a deeper, more interesting bug - that the review pipeline fabricates convincing-looking feedback even when there's no real data behind it. Writing a test that reproduced that exact behavior, then fixing it with a minimal, well-scoped change that didn't touch the placeholder functions themselves, felt like real debugging work rather than just following the issue title literally.
