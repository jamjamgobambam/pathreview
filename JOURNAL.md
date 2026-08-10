# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/97

**Issue title:** Review progress indicator doesn't update in real time during long-running reviews

**Tier:** [x] Tier 3

**Problem summary:**
The review page's progress bar is supposed to reflect the actual status of a
running portfolio review, polled from `GET /reviews/{id}/status` every 5
seconds via the `useReviewStatus` hook. That polling was replaced with a
fixed spinner that never changes, so the progress bar doesn't show real
progress. During long reviews this makes the app look frozen even though
it's still working in the background. The fix affects
`frontend/src/pages/ReviewPage.tsx` and `frontend/src/hooks/useReviewStatus.ts`,
and a successful fix wires the polled status data back into the UI so users
see the review actually advancing in real time instead of a static spinner.

**Branch name:** fix/97-review-progress-realtime

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Reproduction notes (issue #97)

**Steps taken:**
1. Started backing services (`docker compose up -d`) and the app (`make run`), confirmed `http://localhost:5173` and `http://localhost:8000/docs` were reachable.
2. Logged in as `user1@example.com` (seeded test account) and opened the dashboard at `http://localhost:5173/dashboard`.
3. Clicked "Start a New Review", submitted a GitHub username (`octocat`) and a sample resume file, and was redirected to `/reviews/{id}`.
4. Watched the browser's network requests to `GET /api/reviews/{id}/status`, which `useReviewStatus.ts` polls every 3 seconds.

**Observed:**
- Two consecutive polls to `/api/reviews/{id}/status` both returned `{"status":"complete","progress_pct":0}`, meaning even once the review had *fully finished processing*, `progress_pct` was still `0`.
- This confirms the root cause traced in code: `api/routes/reviews.py` (`get_review_status`, ~line 166) returns `getattr(review, "progress_pct", 0)`, but `core/models/review.py`'s `Review` model has no `progress_pct` column, so the `getattr` default (`0`) is always returned. The field is never real data, regardless of pipeline stage.
- Correspondingly, `frontend/src/pages/ReviewPage.tsx` never renders a progress bar or percentage at all. It shows one static "Analyzing your portfolio..." block for the full polling duration, so there's nothing in the UI that could reflect real progress even if the backend sent it.

Full root-cause analysis and fix plan: see `PLAN.md`.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/fcamas/pathreview/commit/d35cca1d23238c43cbd4ed0e113cf4462e7515c5

**Reproduction summary:**
Ran the app locally, logged in, and started a real review through the UI while watching `GET /api/reviews/{id}/status` in the network tab. Two consecutive polls both returned `progress_pct: 0`, even after `status` reached `complete`, confirming `progress_pct` is never populated regardless of pipeline stage.

**PLAN.md link:** https://github.com/fcamas/pathreview/blob/fix/97-review-progress-realtime/PLAN.md

**Walkthrough video (recommended):** Not recorded yet.

**Blockers or open questions:**
Still unsure whether the fix should use fixed milestone percentages (25/50/75/100) at each pipeline stage or something more granular tied to ingestion source count. Plan to confirm against `docs/API.md` before building in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
`docs/API.md` doesn't document a specific contract for `/status`, so went with the simpler fixed-milestone approach from PLAN.md. Implemented the full fix: added the `progress_pct` column and migration, wired `process_review` to advance it 25/50/75/100 across the four pipeline stages (frozen at its last value on any failure path), exposed the real value through the API, and updated `ReviewPage` to render a progress bar and status-aware label instead of the static spinner. Added backend unit tests covering the stage advancement and freeze-on-failure behavior, plus a frontend test suite for the new progress rendering. All sub-tasks from PLAN.md's plan section are done.

**Next steps:**
Run `make check` / `make test-unit`, confirm no regressions against the documented pre-existing failures, open the PR, and get it reviewed before finalizing.

**Blockers:**
Pre-commit's mypy hook blocked the first commit attempt over pre-existing type gaps in the two files this fix touches (and, separately, over an isolated hook environment missing sqlalchemy/pydantic/fastapi). Resolved by fixing the pre-existing annotation gaps and correcting `.pre-commit-config.yaml`'s hook dependencies/scope; documented in the PR description.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/536

**Branch:** `fix/97-review-progress-realtime`

**What you built:**
Added a real `progress_pct` column to `Review`, advanced it through `process_review`'s four pipeline stages instead of leaving it hardcoded at 0, and updated `ReviewPage` to render a live progress bar and status label driven by the polled value instead of a static spinner.

**Tests added or updated:**
`tests/unit/test_review_service.py` (progress_pct initialization, stage advancement, freeze-on-failure) and `frontend/src/pages/__tests__/ReviewPage.test.tsx` (pending/processing/failed rendering, progress bar width).

**Self-review confirmation:** [x] make check passes (no new failures vs. documented pre-existing baseline)  [x] make test-unit passes (53 pre-existing failures unchanged, 4 new tests passing)

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
No review has come in on the PR for issue #97 as of the Week 10 deadline. Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a sign anything is wrong with the submission.

**How you responded:**
N/A, no feedback arrived to respond to. If comments come in after this journal entry is submitted, I'll address them and update this section, but the branch and PR reflect my own self-review (`make check` / `make test-unit`) as the final word for this module.

---

### Reflection

**What was harder than you expected?**
Tracing the bug turned out to be two separate, stacked problems rather than one. The backend never had a real `progress_pct` column to begin with (`getattr(review, "progress_pct", 0)` in `api/routes/reviews.py` was silently falling through to its default every time), and the frontend's `ReviewPage.tsx` didn't render any progress value even if the backend had sent one. It would have been easy to fix only the half I noticed first and ship an incomplete patch. Confirming the second bug required actually watching the Network tab through a full review run and noticing the spinner card was pixel-identical across every poll, which is a kind of confirmation that takes longer than reading the code and assuming you understand it. The pre-commit mypy hook blocking my first commit attempt was also more time-consuming than expected, since it surfaced both a real pre-existing type gap in files I was touching and a broken hook environment (missing sqlalchemy/pydantic/fastapi), and I had to fix the tooling before I could even get my own change committed.

**What did you learn about working in a large codebase?**
Existing patterns matter more than they seem to at first. I didn't invent a new way to persist progress; I followed the migration naming pattern already established by `002_add_error_message_to_reviews.py` and matched the existing status-commit pattern in `process_review()` so the new `progress_pct` commits looked like something a maintainer had written, not a bolted-on afterthought. I also learned that "the code compiles and looks right" isn't the same as "it does what the codebase's own conventions expect." `docs/API.md` didn't document a contract for `/status`, so I had to make a judgment call (fixed 25/50/75/100 milestones instead of granular per-ingestion-source progress) and document that reasoning in PLAN.md rather than just picking one silently.

**How did AI tools help, and where did they fall short?**
AI assistance was most useful for the mechanical parts: scaffolding the Alembic migration against the existing `002_add_error_message_to_reviews.py` pattern, and writing the initial pass of unit tests covering stage advancement and the freeze-on-failure edge case. It was much weaker at the judgment calls. Deciding between fixed milestones and per-source-count granularity wasn't something I could just ask for; I had to check `docs/API.md` myself, confirm it didn't specify a contract, and make the call based on what was simplest to reason about and test. AI also couldn't do the actual repro work: watching real network requests during a live review run to confirm `progress_pct` stayed at 0 through two consecutive polls was something I had to do by hand, in the browser, against the running app.

**What would you do differently if you started over?**
I'd try to reproduce the bug end-to-end in the browser before reading any code, rather than after. I jumped into `api/routes/reviews.py` fairly early because the issue description pointed there, and only did the full manual repro (logging in, starting a real review, watching the Network tab) once I already suspected the root cause. Confirming it blind first would have made me more confident I wasn't missing a second contributing bug (which, in this case, there was: the frontend half). I'd also fix the `.pre-commit-config.yaml` hook dependency issue immediately instead of trying to work around it, since it cost real time mid-week that a five-minute tooling fix up front would have avoided.

**What are you most proud of from this module?**
Catching that this was two bugs, not one. It would have been straightforward to add the `progress_pct` column, wire it through the pipeline, and call the issue closed, since the backend fix alone would have looked complete in a diff. But the frontend was still rendering the same static "Analyzing your portfolio..." block regardless of what the API returned, so a backend-only fix would have shipped and changed nothing a user could see. Catching that gap by actually re-running the repro after the backend change, instead of trusting that the ticket description covered the whole picture, is the part of this module I'd point to as evidence I understood the problem rather than just patched the symptom named in the issue title.
