# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/97

**Issue title:** Review progress indicator doesn't update in real time during long-running reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The review page previously showed a progress bar that reflected actual processing progress by polling `GET /reviews/{id}/status` every few seconds. This was replaced with a static spinner (`Loader` component) that spins indefinitely until the review completes, giving users no indication of how far along the analysis is. The issue lives in `frontend/src/pages/ReviewPage.tsx`, which renders only the spinner during polling, and `frontend/src/hooks/useReviewStatus.ts`, which polls the status endpoint but does not expose any progress data to the UI. A successful fix would restore a progress indicator that updates in real time as the review processes.

**Branch name:** fix/97-review-progress-indicator

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[link to commit documenting the reproduced issue\]](https://github.com/hanluu1/pathreview/commit/7eed904cf9f355b5955eaa413bd869697ec11235)

**Reproduction summary:**
Ran `python tests/repro_issue_97.py`, a static check of the full progress-reporting path — all 5 checks failed, confirming that `progress_pct` is dropped at every layer: no column on the `Review` model, never written by `process_review`, always returns `0` from the status route via a `getattr` fallback, missing from the frontend `Review` TypeScript interface, and `ReviewPage.tsx` renders only a static `<Loader>` spinner with no progress bar during polling.

**PLAN.md link:** [\[link to PLAN.md in your fork\]](https://github.com/hanluu1/pathreview/commit/cd6762aef258140f639b1895ed0c8b66f2da2994)

## Week 9 — Solution building & PR submission
---

### Check-in 2 (end of week)

**PR link:** [\[link to your submitted pull request\]](https://github.com/ascherj/pathreview/pull/967)

**Branch:** [`fix/97-review-progress-indicator`]

**What you built:**
Wired `progress_pct` through the full frontend stack so users see a live progress bar while their portfolio is being analyzed. Added `progress_pct?: number` to the `Review` TypeScript interface, exposed a `progress` value from the `useReviewStatus` hook, and replaced the static `<Loader>` spinner in `ReviewPage.tsx` with a progress bar that fills based on the value returned by the polling endpoint.

**Tests added or updated:**
- write a test file `frontend/src/pages/__tests__/ReviewPage.test.tsx` — covers that a progress bar renders with the correct width and percentage label while polling, and does not appear when polling is inactive.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments arrived on PR #967 before the end of the week, so I have no maintainer feedback to respond to yet.

**How you responded:**
Nothing to respond to yet. While waiting, I self-reviewed my own diff instead: I re-read the three changed frontend files, confirmed `make check` and `make test-unit` still pass on the branch, and wrote down the open questions I expect a reviewer to raise so I can answer them quickly — mainly whether `progress_pct` belongs on the shared `Review` interface or in a dedicated `ReviewStatus` type, since `apiClient.getReviewStatus` claims to return a full `Review` but the endpoint actually returns only `{ review_id, status, progress_pct }`.

---

### Reflection

**What was harder than you expected?**
Tracing the bug was much harder than fixing it. The symptom was one static spinner on one page, but the progress value had to survive five separate layers — the `Review` DB model, `process_review`, the `GET /reviews/{id}/status` route, the frontend `Review` TypeScript interface, the `useReviewStatus` hook, and finally `ReviewPage.tsx`. I had to open files in completely different parts of the repo just to find out where the value was being dropped, and nothing failed loudly along the way: `progress_pct` was silently discarded by TypeScript because the field simply didn't exist on the interface.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code means reading before writing. In my own projects I already know the structure and I have full control, so I can change anything anywhere. Here I had to first understand what the maintainers were building and why, then match their existing conventions — the Tailwind class style already used on the page, the shape the `useReviewStatus` hook already returned, the way other components handled loading state — instead of writing it the way I would have from scratch. I also learned that scope is part of the contribution. I found a real second problem (the backend has no `progress_pct` column, so the value is always `0`), and the right move was to document it in PLAN.md as out of scope rather than expand my PR into the database layer uninvited.

**How did AI tools help — and where did they fall short?**
AI was most useful as a navigator and explainer. It helped me get oriented in an unfamiliar repo quickly, explain code I didn't understand, and point me toward the files where the progress value was flowing (or not flowing). Where it fell short was judgment and verification. It could tell me what the code said, but it couldn't decide for me how much of the problem was mine to fix, whether adding `progress_pct` to the shared `Review` type was acceptable or a hack, or what a maintainer would actually accept in a PR. I also had to verify its claims myself — the type signature on `apiClient.getReviewStatus` says `Promise<Review>` but the endpoint returns something narrower, and I only caught that by reading the backend route directly. The repro script and the risk list in PLAN.md were the parts where I had to think past what AI handed me.

**What would you do differently if you started over?**
I would verify the end-to-end behavior before committing to a plan. I scoped the fix as frontend-only because the status endpoint already returns `progress_pct`, which was technically correct — but because the backend never writes that field, the progress bar I built sits at 0% and then jumps to the finished results. It's still better than a spinner with no information, but it isn't the real-time progress the issue asks for. If I started over I would confirm the backend actually produces real values first, and then either scope the PR to include the missing DB column and the `process_review` updates, or say explicitly in the PR description that this is step one of two. I would also open a draft PR earlier in the week to give a maintainer a chance to weigh in on that scoping question, rather than submitting near the deadline and getting no feedback at all.

**What are you most proud of from this module?**
The reproduction script. Instead of eyeballing the bug in the browser and guessing, I wrote `tests/repro_issue_97.py` to check every layer of the progress path independently, which turned a vague "the spinner doesn't show progress" complaint into five concrete failing checks and a root cause I could point at. That gave me the confidence to write a plan with honest risks and limitations in it, and it's the habit from this module I'd actually carry into the next codebase I'm dropped into.
