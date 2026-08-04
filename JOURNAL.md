# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/97

**Issue title:** Review progress indicator doesn't update in real time during long-running reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a portfolio review is running, the review page only shows a static spinner
with the text "Analyzing your portfolio...", so the user gets no sense of how far
along the review actually is. A previous change replaced a real progress bar with
this spinner, even though the backend already reports progress: the
`GET /reviews/{id}/status` endpoint (in `api/routes/reviews.py`) returns a
`progress_pct` field, and the `useReviewStatus` hook already polls that endpoint
every few seconds. The gap is on the frontend — the `Review` type
(`frontend/src/types/index.ts`) doesn't include `progress_pct`, so the value is
dropped, and `ReviewPage.tsx` renders the spinner instead of a progress bar. A
successful fix threads `progress_pct` through the type and the `useReviewStatus`
hook and renders a live, percentage-driven progress bar during the polling state,
restoring meaningful real-time feedback for long-running reviews.

**Branch name:** fix/97-review-progress-indicator

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — checklist reasoning

- **Scope is bounded and understood.** The fix is concentrated in two frontend
  files (`frontend/src/pages/ReviewPage.tsx`, `frontend/src/hooks/useReviewStatus.ts`)
  plus a small type addition in `frontend/src/types/index.ts`. The backend already
  emits `progress_pct`, so no API or database changes are required — this is
  primarily wiring an existing value through to the UI.
- **I can reproduce and explain it.** I traced the data flow end to end: backend
  returns `progress_pct` → hook polls the status endpoint every 3s → page ignores
  the field and shows a static spinner. That gives me a clear before/after.
- **Tier awareness and skill fit.** This is labeled **Tier 3** (advanced,
  estimated 5–8 hours), which is above the Tier 1 starting point recommended for a
  first contribution. I'm comfortable taking it because the work is frontend React/
  TypeScript — an area I'm confident in — and my end-to-end trace showed the hard
  part (backend progress reporting) is already done, leaving a bounded UI wiring
  task. The main risk is scope creep around "real-time" expectations, so I'm
  keeping the goal narrow: surface the existing `progress_pct` in a progress bar
  during polling, not redesign the review pipeline or add websockets.
- **Open questions / risks to watch:** confirm `progress_pct` is populated during
  processing (not just 0 → 100); decide on graceful fallback if the field is
  missing; add/adjust a test for the hook. These are contained and don't expand
  the blast radius.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Nothoon/pathreview/commit/de1aa0d8928f011e517a0dbbfd976eb1b1e2d7e7

**Reproduction summary:**
I added `tests/repro_issue_97.py`, a stdlib-only script that statically inspects
every file on the progress-reporting path and asserts each gap. Running
`python tests/repro_issue_97.py` reports 4/4 checks FAIL, confirming the issue:
`progress_pct` is dropped at every layer — the `Review` model has no such column,
`process_review` never writes progress, so `get_review_status`'s
`getattr(review, "progress_pct", 0)` is always `0`, the frontend `Review` type
omits the field, and `ReviewPage` renders a static spinner during polling.

**PLAN.md link:** https://github.com/Nothoon/pathreview/blob/fix/97-review-progress-indicator/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Reproduction revealed the fix is broader than the Week 7 frontend-only framing:
the backend reports `progress_pct: 0` on every poll, so the bar would sit at 0%
until complete unless `process_review` emits progress per pipeline stage. Open
question for a mentor: are coarse per-stage milestones (5 fixed values) an
acceptable scope, or is finer progress expected?

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–3 of the five in PLAN.md are done, plus most of 4:

- **Plan step 1 — backend: persist progress.** Added a `progress_pct`
  `Mapped[int]` column to `Review` in `core/models/review.py` with
  `default=0` / `server_default="0"`, and wrote the matching migration
  `alembic/versions/003_add_progress_pct_to_reviews.py`. The server default was
  the risk I flagged in PLAN.md — existing `reviews` rows now read `0` instead of
  `NULL`, so nothing downstream has to handle a missing value.
- **Plan step 2 — backend: emit progress.** `process_review` in
  `core/services/review_service.py` now commits progress at the five milestones
  named in the plan (processing 10, ingestion 35, agent orchestration 60, RAG 85,
  complete 100) through a new `_set_progress` helper that clamps to 0–100. I also
  removed the now-pointless `getattr(review, "progress_pct", 0)` fallback in
  `api/routes/reviews.py::get_review_status`, so the endpoint reads the real
  column.
- **Plan step 3 — frontend: thread the type.** Added `progress_pct?: number` to
  the `Review` interface in `frontend/src/types/index.ts`. No change was needed
  in `useReviewStatus.ts` — it stores the whole `Review`, so the value survives
  to consumers once the type admits it.
- **Plan step 4 — frontend: render the bar (done, still eyeballing styling).**
  The `isPolling` block in `frontend/src/pages/ReviewPage.tsx` now renders a
  percentage-driven bar instead of the static spinner, reusing the existing
  overall-score bar markup, and falls back to the spinner when `progress_pct` is
  absent.

`python tests/repro_issue_97.py` now reports 4/4 PASS (it reported 4/4 FAIL in
Week 8), which is the clearest signal so far that the whole path is wired.

**Next steps:**
Finish plan step 5 (verification): write the unit tests asserting progress
advances during `process_review`, run `make check` and `make test-unit` and
compare them against the pre-change baseline, then open the draft PR, ask for
peer review in Slack, and fill in the PR template.

**Blockers:**
The mentor question from Week 8 (coarse milestones vs. finer progress) is still
unanswered, so I'm shipping the five fixed milestones I planned and calling that
out explicitly in the PR description for the reviewer to push back on.

Two environment notes, neither blocking: this checkout had no `.venv`, so I had
to run `make setup`'s install step before I could run any checks; and `node` is
not installed on this machine, so I verified the frontend change by reading the
rendered JSX path and its type-checking rather than by running `npm test`.

---

### Check-in 2 (end of week)

**PR link:** _(TODO: paste the PR URL here once the pull request is opened)_

**Branch:** `fix/97-review-progress-indicator`

**What you built:**
Review progress is now reported end to end instead of being dropped at every
layer. `process_review` persists a `progress_pct` value on the new `reviews`
column at five pipeline milestones (10/35/60/85/100), `GET /reviews/{id}/status`
returns that live column instead of a hardcoded `0`, and `ReviewPage` renders a
percentage-driven progress bar during polling — clamped to 0–100, snapped to 100
on completion, and falling back to the old spinner when the field is absent.

**Tests added or updated:**
`tests/unit/test_review_service.py` — added a `TestReviewProgress` class (8
tests) covering: `process_review` committing the exact milestone sequence
10 → 35 → 60 → 85 → 100 in order; progress never decreasing and staying inside
0–100; the review ending at `status="complete"` with `progress_pct=100`; at least
three distinct intermediate values being observable mid-run (the direct
regression guard for #97, where every poll returned `0`); a review failed by
safety checks keeping its partial progress instead of jumping to 100;
`create_review` starting a new review at `progress_pct=0`; and `_set_progress`
clamping out-of-range values (150 → 100, −20 → 0) and committing so polls can
observe the value.

`tests/repro_issue_97.py` — the Week 8 reproduction script now reports 4/4 PASS
instead of 4/4 FAIL (unchanged file, used as a before/after check).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both boxes reflect the "no new failures" standard for a codebase with documented
pre-existing failures. Measured on `9e32d4c` (the commit before my changes) and
again on the branch tip:

| Command | Before | After |
| --- | --- | --- |
| `ruff check .` (`make lint`) | 182 errors | 182 errors |
| `black --check .` | 53 files would reformat | 53 files would reformat (none of them mine) |
| `mypy api/ core/ ingestion/ rag/ agent/ safety/` | 5 errors in 4 files | 5 errors in 4 files |
| `pytest tests/unit -m unit` (`make test-unit`) | 53 failed, 375 passed | 53 failed, **383 passed** |

Same failures before and after; the only delta is my 8 new passing tests. The
pre-existing failures are missing type stubs (`jose`, `passlib`, `rank_bm25`,
`PyPDF2`), a numpy stub that needs Python ≥3.12, and 53 unit tests that already
failed on `main` — including 13 in `test_review_service.py::TestReviewService`
that mis-mock the async session (`AsyncMock` result objects make
`result.scalars()` a coroutine). I left those alone: they're unrelated to #97 and
fixing them would balloon the diff.

**Draft PR feedback received from:** none (no peer or mentor feedback received at
the time of submission)
