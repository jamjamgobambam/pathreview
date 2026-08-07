## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for `core/services/review_service.py` is below 40%

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
The review service is the most critical orchestration layer in the application,
handling creation, retrieval, listing, and deletion of reviews. Despite its
importance, most of its code paths have no unit tests, leaving coverage below
40%. The fix requires writing pytest unit tests targeting the major execution
paths in `core/services/review_service.py` — including success cases, partial
failure, and full failure scenarios — until coverage meaningfully exceeds the
40% threshold.

**Branch name:** feat/109-review-service-test-coverage

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Is this right for me? — checklist reasoning:**

- Scope is contained to one file: `tests/unit/test_review_service.py`
- No linked PRs exist; issue is unclaimed
- Pytest + async mocking skills match prior work (Mixtape Bug Hunt)
- Estimated effort (5–7 hrs) fits the Week 7–8 timeline
- Read `core/services/review_service.py` locally to confirm the functions exist

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/franklinproject10/pathreview/commit/d4a5969

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py -v` and observed 13 of 19 tests
failing with `AttributeError: 'coroutine' object has no attribute 'first'`.
The existing mocks used `AsyncMock` for the full result chain including
`.scalars()` and `.first()`, which are synchronous methods on an already-awaited
result. Running coverage confirmed the service was below 40%.

**PLAN.md link:**
https://github.com/franklinproject10/pathreview/blob/feat/109-review-service-test-coverage/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Pre-existing mypy errors in `core/services/review_service.py` block the
pre-commit hook — these are out of scope for this issue. Private helper
functions remain untested; coverage could be pushed to ~85%+ by adding
tests for `_run_ingestion_pipeline` and `_run_safety_checks` in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all sub-tasks from PLAN.md. Fixed broken async mock chain in test_review_service.py, bringing coverage from below 40% to 69%. Opened draft PR #985 on ascherj/pathreview.

**Next steps:**
Request peer or mentor feedback on the draft PR, then mark ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/985

**Branch:** `feat/109-review-service-test-coverage`

**What you built:**
Added 8 unit tests for `ReviewService.process_review` in `core/services/review_service.py`. Fixed a broken async mock chain (AsyncMock applies only to `execute()`; `.scalars()` and `.first()` are synchronous result-chain methods). Coverage raised from below 40% to 69%.

**Tests added or updated:**
`tests/unit/test_review_service.py` — covers successful review completion, exception handling, status transitions, and database interaction patterns.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.] - No reviewer feedback was received. Per the Summer 2026 course note, reviewer feedback is not a provided feature this term, and my PR (#985) remained awaiting maintainer review on ascherj/pathreview through the end of the module.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.] - N/A — there was no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

I expected the hard part of a test-coverage issue to be writing tests — thinking up cases, hitting edge conditions. Instead, the hard part was that the existing test setup for review_service.py was silently broken, and I had to understand why before I could add anything. The mock chain wrapped the entire SQLAlchemy call in AsyncMock, but only execute() actually returns a coroutine — .scalars() and .first() are synchronous result-chain methods. So await-ing the wrong link blew up in a way that didn't point at the real cause. What made it genuinely hard was that the error message pointed downstream of the actual mistake, so I spent real time looking in the wrong place. Once it clicked — the coroutine is the ticket stub, not the meal — I stopped treating a mock as one black box and started asking of every link in the chain, "does this return a coroutine or a plain value?" That reframing is the thing I actually took away, more than the fix itself.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

What did you learn about working in a large codebase?

In my own projects, every file is one I put there, so "what's in scope" is never a question — it's all mine. Contributing to PathReview flipped that. When I went to commit, the pre-commit hook failed on mypy type errors that were already in review_service.py before I touched it. My instinct was to fix them, but that would've meant editing code unrelated to issue #109 and ballooning a focused test-coverage PR into a cleanup PR nobody asked for. Learning to use --no-verify deliberately — and to document why — taught me that in a shared codebase, restraint is a skill. The discipline isn't "fix everything you see," it's "fix exactly what your issue claims and leave a clear trail for the maintainer explaining what you consciously left alone." Contributing to someone else's production code is less like building and more like surgery: you touch only what you came to touch, because every extra change is something a reviewer now has to vet and trust.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

AI was most useful as a concept translator. When the async mock chain was breaking, having the coroutine-vs-synchronous distinction explained through an analogy — the coroutine is a ticket stub you redeem, not the meal itself — made a confusing error legible in a way that reading the SQLAlchemy docs cold didn't. It was strong at "here's the mental model for why this fails." Where it fell short was everything downstream of understanding. It couldn't run my tests, couldn't see that coverage had actually moved from under 40% to 69%, and couldn't confirm the mock behaved right against the real service — I had to run pytest and verify that myself. It also fell short in a literally mechanical way: pasting large code blocks into VS Code silently corrupted them, eating spaces around punctuation, so "help" I trusted introduced bugs I then had to hunt. The lesson was that AI accelerates comprehension, but verification stays my job — the model can hand me a map, but I'm still the one who has to walk the ground and confirm it's accurate.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I'd change how I moved code between the AI conversation and my editor. Early on I pasted large blocks straight into VS Code, and the paste silently corrupted them — spaces vanished around punctuation — which meant I was debugging failures that weren't logic errors at all, just transfer artifacts. That's time I spent chasing ghosts. Starting over, I'd default to writing generated code to a file and copying from there, treating paste as unreliable for anything longer than a few lines. More broadly, I'd front-load the boring setup verification: confirm the project fully builds and the existing tests run before writing anything, so that when something breaks later I can trust it's my change and not inherited state. The theme of both is the same — spend a little time up front removing sources of ambiguity, so that when a test fails, the failure actually means what I think it means.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]

I'm most proud that I fixed the broken mock chain by actually understanding it, not by pattern-matching my way around it. The easy path would've been to keep tweaking AsyncMock placements until the errors stopped and the tests went green — green tests, no real comprehension. Instead I made myself answer why each link in the chain returned a coroutine or a plain value before I changed anything, and that understanding is what let coverage climb from under 40% to 69% on a foundation I actually trust. The number is the visible result, but the thing I'm proud of is the discipline behind it: I treated "make it pass" and "understand why it passes" as two different bars, and I held myself to the second one.
