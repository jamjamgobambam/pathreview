## Solution plan

**Issue:** Review progress indicator doesn't update in real time during long-running reviews (#97)  
link: https://github.com/ascherj/pathreview/issues/97

### Understand

During a long-running review, the frontend displays only a static loading spinner instead of meaningful progress updates.

The current flow has several gaps:

1. `core/models/review.py` does not define a persisted `progress_pct` field.
2. `core/services/review_service.py` does not calculate or store progress as the review moves through its processing stages.
3. `api/routes/reviews.py` returns `progress_pct` using `getattr(review, "progress_pct", 0)`, so the endpoint currently returns `0` through its fallback because no persisted progress field exists.
4. The frontend status response is not modeled cleanly in TypeScript, even though the runtime JSON retains the `progress_pct` field.
5. `frontend/src/pages/ReviewPage.tsx` renders only the static “Analyzing your portfolio...” loading state while polling.

The expected behavior is for the existing polling flow to return meaningful progress values that the review page can render as the review advances.

### Map

The main files involved are:

- `core/models/review.py` - persist review progress.
- `core/services/review_service.py` - update progress during review processing.
- `api/routes/reviews.py` - return the persisted progress value from the status endpoint.
- `api/schemas/review.py` - define a clean status-response contract if needed.
- `alembic/versions/<new_revision>_add_progress_pct_to_reviews.py` - migrate the database schema.
- `frontend/src/types/index.ts` - represent the review status response correctly.
- `frontend/src/services/api.ts` - type the status API response.
- `frontend/src/hooks/useReviewStatus.ts` - update status-response typing while keeping the existing polling behavior.
- `frontend/src/pages/ReviewPage.tsx` - render the progress indicator.
- `tests/unit/test_review_service.py` - cover backend progress behavior.
- `frontend/src/pages/__tests__/ReviewPage.test.tsx` - cover progress rendering.

### Plan

1. **Add durable progress storage.**  
   Add a `progress_pct` field to the `Review` model and create an Alembic migration that initializes existing records safely, including completed reviews.

2. **Track progress during processing.**  
   Update `process_review` to persist coarse, monotonic progress milestones at the existing processing-stage boundaries. Commit intermediate values so polling requests can observe them.

3. **Expose and type the status response.**  
   Update the backend status response and frontend TypeScript types so `progress_pct` is represented cleanly without treating the narrow `/status` response as a full review object.

4. **Render progress in the review page.**  
   Replace the static-only loading experience with an accessible percentage-driven progress bar while preserving the existing completed and failed review states.

5. **Add focused regression coverage.**  
   Add backend tests for initialization, milestone progression, completion, and failure behavior, plus frontend tests for progress-bar rendering. Compare results against the documented baseline failures so the fix introduces no new regressions.

### Inputs & outputs

**Inputs:**

- A newly created review beginning in the pending state.
- Background execution of the existing review-processing pipeline.
- Polling requests to `GET /reviews/{id}/status`.

**Outputs:**

- A persisted progress value for each active review.
- A status response containing meaningful progress information.
- A review page that reflects the latest polled progress value and updates as new polling results arrive.
- Existing completed and failed review behavior continuing to work as before.

### Risks & unknowns

- The current mock pipeline completes very quickly, so intermediate progress values may not be visually observable within the 3-second polling interval even when they are persisted correctly.
- The progress percentages will represent coarse stage milestones rather than measured estimates of remaining execution time.
- The database migration must be applied before backend code depends on the new column.
- The `/status` response currently uses a narrower shape than the frontend `Review` type, so the typing should be corrected without expanding this into a larger API refactor or creating inaccurate TypeScript assumptions about the response shape.
- The repository already has unrelated baseline test failures. Week 9 verification should confirm that this change introduces no new failures.
- The existing background-task database-session lifecycle is a broader architectural concern and will remain out of scope unless it directly blocks this fix.

### Edge cases

- Newly created reviews should begin at `0%`.
- Progress should increase monotonically and remain within `0–100`.
- Completed reviews should persist `progress_pct = 100` together with `status = "complete"`.
- Failed reviews should retain their last meaningful progress value rather than incorrectly jumping to `100`.
- Historical completed rows should receive sensible progress values during migration.
- Missing or unexpected progress values should not break the frontend layout.
- The page should continue transitioning correctly from the polling state to either the completed review or the existing failure UI.