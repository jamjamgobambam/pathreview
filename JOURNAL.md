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
