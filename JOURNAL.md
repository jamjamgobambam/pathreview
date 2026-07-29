# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When two review requests come in for the same profile at almost the same time, both kick off the agent review loop against whatever profile state is currently in the database, with no coordination between the two runs. If the first request modifies the profile mid-flight, the second loop can still be working from the state it read before that change, so its output doesn't reflect the latest data. The fix is to add a per-profile lock so a second review request for the same profile is serialized behind the first instead of running concurrently against shared state. This mainly touches the review submission endpoint in `api/routes/reviews.py` and the orchestration logic in `core/services/review_service.py`.

**Is this right for me? — checklist reasoning:**

- *Understanding the issue:* When a user fires off two review requests for the same profile close together, both spawn independent `process_review` background tasks that read and write the same profile/review state with no coordination between them. Whichever task's writes land last wins, so the first task's work can be silently overwritten, or the second task can act on ingestion/profile data the first task already changed underneath it. "Done" looks like: submitting two reviews for the same profile back-to-back no longer risks one clobbering or reading stale state from the other — the second request waits for the first to finish before it starts.
- *Tier fit:* This is my first *open-source* contribution, but not my first time in a large codebase — I have around 2 years of professional experience, including work on production systems with concurrency bugs similar to this one so this is a considered Tier 3 pick, not a "challenge myself" pick.
- *Codebase readiness:* Read `create_review_endpoint` in `api/routes/reviews.py` (creates the review row, then fires `process_review` via an unguarded `BackgroundTasks.add_task` call — no locking or dedup on `profile_id`) and `process_review` in `core/services/review_service.py` (reads the profile, runs ingestion → agent orchestration → RAG → safety checks → writes `review.status`/`sections`, with no per-profile synchronization anywhere in that path). Confirmed the race concretely: two requests for the same `profile_id` each call `_run_ingestion_pipeline`, which writes its own `IngestedSource` rows and commits independently, so concurrent runs duplicate ingestion data. Checked `tests/unit/test_review_service.py` — it only covers `create_review`, `get_review`, and `list_reviews` with mocked DB sessions; there is no existing coverage for `process_review` or any concurrency behavior, so tests for this fix will need to be written from scratch (likely simulating two concurrent `process_review` calls with `asyncio.gather`).
- *Scope and time:* No "blocked by" language or dependencies found on the issue. Since there's no existing lock/concurrency pattern in the codebase to follow and no test coverage to build from, I'm budgeting toward the higher end of the 6–9 hour estimate.

**Branch name:** fix/82-concurrent-review-race-condition

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/janellycedenoaquino/pathreview/commit/944628f

**Reproduction summary:**
Wrote an integration test (`tests/integration/test_review_service.py`) that runs two `process_review` calls concurrently for the same profile, patching the agent-orchestration step to take a fixed 0.3s so overlap is deterministic. The test asserts the second review only starts processing after the first finishes -- this currently fails (both start before either finishes), confirming `process_review` has no per-profile lock.

**PLAN.md link:** https://github.com/janellycedenoaquino/pathreview/blob/fix/82-concurrent-review-race-condition/PLAN.md

**Walkthrough video (recommended):** [not recorded yet]

**Blockers or open questions:**
- Still deciding between two ways to hold the Postgres advisory lock across `process_review`'s pipeline: consolidate its several intermediate `db.commit()` calls into one final commit (bigger change), vs. use session-scoped `pg_advisory_lock`/`pg_advisory_unlock` explicitly with a `finally` release (smaller change, more manual bookkeeping). Leaning toward the latter but not settled.
- Found two pre-existing bugs unrelated to #82 while building the reproduction: `core/services/review_service.py` fails `mypy` on `main` independent of any of my changes, and `_run_ingestion_pipeline` passes a `raw_data` kwarg that doesn't exist on the `IngestedSource` model (silently swallowed, so ingestion never actually writes rows today). Neither blocks the Week 9 fix, but flagging in case a mentor wants these reported separately.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five `PLAN.md` sub-tasks are done. Added `_acquire_profile_lock`, which acquires a Postgres advisory lock (`pg_advisory_xact_lock`, keyed on `profile_id` via `hashtext()`) in `process_review` right after the existing "processing" status commit. Resolved the multi-commit/lock-scope conflict flagged in Week 8 by removing the internal `db.commit()` inside `_run_ingestion_pipeline`, so the transaction-scoped lock now spans the whole ingestion → agent → RAG → safety pipeline through to a single terminal commit. The Week 8 reproduction test now passes with no changes to the test itself, and I added a second test confirming the lock is scoped per-profile (different profiles don't block each other). Ran `make check`/`make test-unit` before and after the change and diffed the failure lists to confirm zero new regressions. Opened a draft PR for early feedback: https://github.com/ascherj/pathreview/pull/229

**Next steps:**
Share the draft PR in the cohort feedback channel. Once I've either incorporated feedback or decided I'm satisfied without any, mark it ready for review and complete Check-in 2 with the final PR link.

**Blockers:**
None blocking my own progress. For context (not blocking): the repo has some pre-existing issues unrelated to #82 -- `core/services/review_service.py` fails `mypy` independent of this change, `make check`'s lint step has ~181 pre-existing ruff errors repo-wide in files this PR doesn't touch, and `tests/unit` has 53 pre-existing failures (confirmed identical before/after). All documented in the PR description under "Pre-existing issues."

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/229

**Branch:** fix/82-concurrent-review-race-condition

**What you built:**
`process_review` in `core/services/review_service.py` now acquires a Postgres advisory lock (`pg_advisory_xact_lock`, keyed on `profile_id`) right after the "processing" status commit and holds it for the rest of the pipeline, so a second review for the same profile waits for the first to finish instead of running concurrently against shared state. Reviews for different profiles are unaffected and still run in parallel.

**Tests added or updated:**
`tests/integration/test_review_service.py` -- the Week 8 reproduction test (`test_concurrent_reviews_for_same_profile_are_not_serialized`) now passes unmodified, confirming the lock serializes same-profile reviews. Added `test_concurrent_reviews_for_different_profiles_are_not_blocked` to confirm the lock is scoped per-profile, not global.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(No new failures introduced -- pre-existing failures documented in the PR description under "Notes for Reviewers" and confirmed identical before/after this change.)

**Draft PR feedback received from:** none received yet -- PR was opened as a draft for early feedback, then moved to ready for review before any feedback arrived. Will note in the Week 10 reflection if anything comes in after submission.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
N/A -- No reviewer feedback.

**How you responded:**
N/A --No feedback.

---

### Reflection

**What was harder than you expected?**
Two things. First, just getting a stable local environment took longer than the fix itself -- a Docker Compose port conflict caused by a completely unrelated, native PostgreSQL 18 install on the exact port the project wanted, which `lsof` couldn't even see without sudo. Second, picking the *right* locking mechanism was harder than picking *a* locking mechanism. My first instinct (a session-scoped `pg_advisory_lock`) looked reasonable until I worked through how SQLAlchemy's connection pooling actually behaves under concurrency -- it doesn't guarantee the same physical connection stays checked out across multiple commits, which means that lock could silently protect nothing under real load while still looking like it worked in casual testing. That's a genuinely scary failure mode for a fix whose entire job is correctness under concurrency.

**What did you learn about working in a large codebase?**
Most of the actual work wasn't writing code -- it was verifying claims instead of assuming them. Tracing exactly which functions called `_run_ingestion_pipeline` before touching its transaction behavior. Actually diffing the full `tests/unit` failure list before and after my change instead of checking it looked the same. Checking whether the frontend actually rendered the "processing" status differently from "pending" before assuming it was safe to change when that status became visible. Large codebases punish assumptions in a way a solo project never does, because you can't see all the consumers of a function just by reading the function.

**How did AI tools help — and where did they fall short?**
AI was strongest at fast, systematic investigation -- tracing call graphs, running reproduction and regression tests, diffing baselines, drafting the actual lock code once a design was settled. It fell short at the actual judgment calls, and needed real pushback from me to get right: it initially proposed "fixing" pre-existing mypy debt in functions unrelated to my change just to satisfy a pre-commit hook, which I had to catch and reject as scope creep. It also initially misdiagnosed the Docker port conflict (assumed restarting Docker Desktop would fix it) before the real root cause -- a native Postgres install -- was actually found. AI is good at generating plausible next steps; however i had to verify the *right* ones, not just the most immediately available ones.

**What would you do differently if you started over?**
I'd try to get the local Docker environment fully stable before committing to a Tier 3 issue, since a real chunk of early time went into unrelated environment debugging rather than the actual problem.

**What are you most proud of from this module?**
Catching that the "obvious" locking approach had a subtle correctness bug before writing a single line of it. It would have been easy to implement the session-scoped lock, watch the reproduction test pass, and ship it -- and it might have looked completely fine in review. The bug only would have shown up under real concurrent production load, which is exactly the scenario the original issue was about. Reasoning through *why* it was wrong instead of just going with the first thing that worked in testing is the part of this module I'd point to as real engineering judgment, not just following steps.
