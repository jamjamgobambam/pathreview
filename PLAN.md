# Solution plan

**Issue:** Review progress indicator doesn't update in real time during long-running reviews — https://github.com/ascherj/pathreview/issues/97

### Understand

**Expected:** While a portfolio review is processing, the review page shows a
live progress bar that advances as the backend works through its pipeline
(ingestion → agent orchestration → RAG generation → safety checks), giving the
user a real sense of how far along the review is.

**Actual:** The review page shows a static spinner with the text "Analyzing your
portfolio..." for the entire run, then jumps straight to the finished review. No
percentage, no movement.

**Root cause (confirmed by reproduction — `tests/repro_issue_97.py`, all 4 checks FAIL):**
The progress value is dropped at *every* layer of the path, not just one:

1. **Backend model** — `core/models/review.py` has no `progress_pct` column.
2. **Backend service** — `core/services/review_service.py::process_review` only
   flips `status` `pending → processing → complete`; it never writes a progress
   value between pipeline steps.
3. **Backend endpoint** — `api/routes/reviews.py::get_review_status` returns
   `getattr(review, "progress_pct", 0)`. Because the column doesn't exist, this
   silently resolves to `0` on every poll.
4. **Frontend type** — `frontend/src/types/index.ts` `Review` interface omits
   `progress_pct`, so even a real value would be dropped by the hook.
5. **Frontend render** — `frontend/src/pages/ReviewPage.tsx` renders an
   `animate-spin` `Loader` during `isPolling` and never reads `progress_pct`.

So the Week 7 assumption ("backend already reports progress, this is frontend
wiring only") is only half true: the endpoint *has the field name* but the value
is hardcoded to `0`. Wiring the frontend alone would produce a bar frozen at 0%
until it snaps to complete. The fix must emit progress on the backend **and**
thread it through the frontend.

### Map

Files I expect to touch:

- `core/models/review.py` — add a `progress_pct` column to the `Review` model.
- `alembic/versions/<new>.py` — new migration adding the `progress_pct` column.
- `core/services/review_service.py` — set `review.progress_pct` at each pipeline
  step in `process_review` (and commit) so polls observe advancing values.
- `api/routes/reviews.py` — `get_review_status` already returns `progress_pct`;
  verify it now reads a real column instead of the `getattr` fallback.
- `frontend/src/types/index.ts` — add `progress_pct?: number` to `Review`.
- `frontend/src/hooks/useReviewStatus.ts` — no field-specific change needed
  (it stores the whole `Review`), but confirm the value survives to consumers.
- `frontend/src/pages/ReviewPage.tsx` — replace the static spinner in the
  `isPolling` block with a percentage-driven progress bar.
- `tests/unit/test_review_service.py` — assert progress advances during
  processing.
- `tests/repro_issue_97.py` — the reproduction checks flip to PASS after the fix.

### Plan

1. **Backend: persist progress.** Add `progress_pct: Mapped[int]` (default `0`)
   to the `Review` model and generate an Alembic migration for the new column.
2. **Backend: emit progress.** In `process_review`, set and commit
   `review.progress_pct` at each milestone — e.g. `processing`=10, after
   ingestion=35, after agent orchestration=60, after RAG=85, `complete`=100 — so
   each 3s poll returns a changing value.
3. **Frontend: thread the type.** Add `progress_pct?: number` to the `Review`
   interface so the hook stops dropping it.
4. **Frontend: render the bar.** In `ReviewPage.tsx`, replace the spinner-only
   `isPolling` block with a progress bar driven by
   `statusReview?.progress_pct` (reusing the existing overall-score bar markup),
   falling back to an indeterminate style when the value is missing.
5. **Verify.** Re-run `python tests/repro_issue_97.py` (expect all PASS), add a
   `process_review` progress assertion to `tests/unit/test_review_service.py`,
   and manually confirm the bar advances against a running review.

### Inputs & outputs

- **Backend input:** the in-flight `Review` row and the pipeline stage reached in
  `process_review`. **Output:** `review.progress_pct` (int `0–100`) persisted and
  committed at each stage; `GET /reviews/{id}/status` now returns that live value
  instead of a constant `0`. This changes the *value* of the existing
  `progress_pct` field in the status response, not the response shape.
- **Frontend input:** the `Review` object from `useReviewStatus`, now carrying
  `progress_pct`. **Output:** a rendered `<div>` progress bar whose width is
  `${progress_pct}%` during the `isPolling` state, replacing the static spinner.
- **No change** to the request signatures of `getReviewStatus`/`getReview` or to
  the DB schema beyond the single additive `progress_pct` column.

### Risks & unknowns

- **Migration on existing rows** (`alembic/versions/*`, `core/models/review.py`):
  the new column needs a server-side default (`0`) so existing `reviews` rows and
  the `getattr` fallback path don't break; a nullable-without-default column would
  make old rows read `None` and crash the width calc.
- **Backend scope creep** (`core/services/review_service.py`): the issue was
  framed as frontend-only, but reproduction shows the value is `0`. I need to
  confirm with a mentor whether emitting coarse per-stage progress (5 fixed
  milestones) is acceptable, or whether they expect finer granularity — I'm
  keeping it to fixed milestones to stay bounded and avoid touching the pipeline
  internals in `_run_ingestion_pipeline` / `_run_agent_orchestration`.
- **Commit frequency** (`process_review`): adding a DB commit per stage is extra
  write load; unknown whether the reviewers want that vs. a single in-memory
  field updated less durably. Fixed milestones (≤5 commits) keep it modest.
- **Polling race** (`frontend/src/hooks/useReviewStatus.ts`): the hook stops
  polling on `complete`/`failed`; I must make sure the bar reaches 100% on the
  last successful poll and doesn't get stuck at 85% if `complete` arrives in the
  same tick as the jump to the full review view.
- **`error_message`/`failed` path** (`ReviewPage.tsx`): the progress bar must not
  render (or must reset) when `status === 'failed'`, which currently renders in a
  separate block.

### Edge cases

- **`progress_pct` missing / `undefined`** (old review, or backend not yet
  deployed): render an indeterminate bar or fall back to the current spinner
  rather than a `NaN%` width.
- **`progress_pct === 0`** at the very start of processing: show an empty-but-
  present bar, not a broken/invisible element.
- **`status === 'failed'` mid-progress** (e.g. failed at 60%): hide the progress
  bar and show the existing "Review Failed" block instead of a stuck partial bar.
- **`status === 'complete'` while the bar still reads < 100**: clamp the
  displayed value to 100 on completion so it doesn't freeze partway.
- **Value out of range** (`< 0` or `> 100` from a backend bug): clamp to
  `[0, 100]` before setting the bar width.
- **Very fast review** (completes before the first 3s poll): user may never see
  intermediate values — the completed view must still render correctly with no
  leftover progress UI.
