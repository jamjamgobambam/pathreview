# Solution plan

**Issue:** [#97: Review progress indicator doesn't update in real time during long-running reviews](https://github.com/ascherj/pathreview/issues/97)

### Understand

**Expected behavior:** While a review is running, the UI should show the user real, advancing progress (e.g. a percentage or a step label) so long reviews don't look frozen.

**Actual behavior:** The progress indicator never changes. Root cause is two separate bugs stacked on top of each other:

1. **Backend never computes real progress.** `GET /reviews/{id}/status` (`api/routes/reviews.py:139-176`) returns `"progress_pct": getattr(review, "progress_pct", 0)`. The `Review` SQLAlchemy model (`core/models/review.py`) has no `progress_pct` column, so `getattr` always falls through to its default and the field is hardcoded to `0`. `process_review()` in `core/services/review_service.py` runs four real pipeline stages between `processing` and `complete` (ingestion → agent orchestration → RAG retrieval/generation → safety checks) but never updates any progress value at any of those steps.
2. **Frontend doesn't render what it does have.** `useReviewStatus.ts` polls `/status` correctly every 3s and does update `review.status` (`pending` → `processing` → `complete`/`failed`). But `ReviewPage.tsx` renders one static block ("Analyzing your portfolio... This may take a few moments") for the entire time `isPolling` is true, regardless of `status` or any progress value. Confirmed via manual repro: the Network tab showed `progress_pct: 0` on every poll, and the spinner card was pixel-identical across all polls until the page jumped straight to the finished report.

A correct fix needs both: the backend must persist and expose a real progress signal, and the frontend must display it.

### Map

- `core/models/review.py`: add a `progress_pct` (or similar) column to the `Review` model.
- `alembic/versions/`: new migration adding that column (pattern: `003_add_progress_pct_to_reviews.py`, following `002_add_error_message_to_reviews.py`).
- `core/services/review_service.py`: `process_review()` (lines ~82-194), update `review.progress_pct` and commit at each of the four pipeline stages (ingestion, agent orchestration, RAG, safety checks) instead of only ever touching `status`.
- `api/routes/reviews.py`: `get_review_status` (lines 139-176), return the real column value instead of the `getattr(..., 0)` fallback.
- `api/schemas/review.py`: decide whether `ReviewResponse`/status response needs `progress_pct` typed explicitly.
- `frontend/src/types/index.ts`: add `progress_pct` to the `Review` interface.
- `frontend/src/hooks/useReviewStatus.ts`: confirm it passes the new field through untouched (likely no change needed, but verify).
- `frontend/src/pages/ReviewPage.tsx`: replace the static "Analyzing..." block with one that reflects `statusReview.status` and `statusReview.progress_pct` (e.g. a progress bar plus a status-specific label for `pending` vs `processing`).
- `tests/unit/test_review_service.py`: extend/add tests asserting `progress_pct` advances through the pipeline stages.

### Plan

1. Add `progress_pct` column to `Review` model, then write and run the Alembic migration. Verify with `alembic upgrade head` and a manual `psql`/`\d reviews` check.
2. Update `process_review()` in `review_service.py` to set `review.progress_pct` (e.g. 25/50/75/100) and commit at each of the four stage boundaries, matching the existing status-commit pattern.
3. Update `get_review_status` in `api/routes/reviews.py` to return the real `review.progress_pct` value instead of the hardcoded fallback; add `progress_pct` to the relevant schema.
4. Add `progress_pct` to the frontend `Review` type and update `ReviewPage.tsx` to render a progress bar / distinct status text driven by `statusReview.status` and `statusReview.progress_pct`.
5. Write/extend unit tests in `tests/unit/test_review_service.py` covering progress advancing through each stage, and manually re-run the Step 2 repro to confirm the Network tab now shows increasing `progress_pct` values and the UI visibly updates.

### Inputs & outputs

- **Input:** an in-flight `Review` row being advanced through `process_review()`'s four pipeline stages; on the frontend, the polled JSON body from `GET /reviews/{id}/status`.
- **Output (backend):** `review.progress_pct` persisted in Postgres and returned by `/status` as a real, increasing integer (0 to 100) instead of a hardcoded 0; existing `status` field behavior is unchanged.
- **Output (frontend):** `ReviewPage.tsx` renders a progress bar/percentage and a status-aware label that visibly changes across polls instead of one static spinner card.

### Risks & unknowns

- **Migration risk:** adding a non-nullable column to `reviews` needs a default (e.g. `default=0`) so existing rows and the `create_review` insert path (`core/services/review_service.py` around line 21-25) don't break. Need to check `create_review()` initializes `progress_pct=0` explicitly.
- **Stage-boundary granularity is a judgment call:** unsure whether reviewers want fixed milestones (25/50/75/100) or something more granular per ingestion source count in `_run_ingestion_pipeline` (`core/services/review_service.py:197+`). Worth confirming against `docs/API.md` if it documents an expected contract for `/status`.
- **Concurrent DB writes:** `process_review` already does multiple `db.add(review); await db.commit()` calls per run. Need to confirm adding more commits mid-pipeline doesn't introduce race conditions if a user triggers a second review concurrently (shared `db` session handling in background tasks is worth re-checking in `core/database.py`).
- **Frontend polling cadence:** `useReviewStatus.ts` polls every 3s; if a pipeline stage completes faster than that, the UI may still look like it "jumps" between values. May be acceptable, but worth calling out as a known limitation rather than something to over-engineer.

### Edge cases

- Review fails mid-pipeline (`status="failed"` at any of the four stages): `progress_pct` should freeze at its last real value, not reset to 0 or jump to 100.
- Review created but never picked up by `process_review` yet (`status="pending"`): `progress_pct` should read 0, and the frontend should show a distinct "queued" state rather than the same "processing" label.
- Existing reviews created before the migration (no `progress_pct` set): must default sanely (0 or 100 if already `complete`) rather than erroring on `NULL`.
- Frontend receives a `progress_pct` that doesn't monotonically increase (e.g. due to a retried stage): UI should not visually regress the bar backward in a jarring way.
