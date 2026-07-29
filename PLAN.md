## Solution plan

**Issue:** Review progress indicator doesn't update in real time during long-running reviews
https://github.com/ascherj/pathreview/issues/97

### Understand

**Root cause:** The backend `GET /reviews/{id}/status` endpoint already returns `progress_pct`, but the frontend discards it at every layer. The `Review` TypeScript interface has no `progress_pct` field, so the value is silently dropped when the API response is parsed. The `useReviewStatus` hook never exposes it, and `ReviewPage.tsx` has no progress bar — only a static `<Loader>` spinner that spins until the review completes.

**Expected behavior:** A progress bar that fills from 0% to 100% as the review processes, updating every time the status endpoint is polled (every 3 seconds).

**Actual behavior:** A spinner that shows no progress information whatsoever.

### Map

| File | What needs to change |
|---|---|
| `frontend/src/types/index.ts` | Add `progress_pct?: number` to the `Review` interface |
| `frontend/src/hooks/useReviewStatus.ts` | Expose `progress` in the hook's return value |
| `frontend/src/pages/ReviewPage.tsx` | Replace static `<Loader>` spinner with a progress bar |

No backend changes are needed — the status endpoint already returns `progress_pct`. The value is always `0` because the `Review` DB model has no such column (`getattr` fallback), but wiring real progress updates in the backend is a separate concern outside this issue's scope.

### Plan

1. Add `progress_pct?: number` to the `Review` interface in `frontend/src/types/index.ts`
2. Update `UseReviewStatusReturn` in `useReviewStatus.ts` to include `progress: number`, derived from `review?.progress_pct ?? 0`
3. Return `progress` from the hook
4. Destructure `progress` from `useReviewStatus` in `ReviewPage.tsx`
5. Replace the `isPolling` spinner block with a progress bar that renders `style={{ width: `${progress}%` }}`

### Inputs & outputs

**Input:** `progress_pct` (0–100) from `GET /reviews/{id}/status` response, polled every 3 seconds while `isPolling` is true.

**Output:** A filled progress bar and percentage label visible to the user during processing. When `isPolling` stops and the review is complete, the results display as before.

### Risks & unknowns

- `progress_pct` will always be `0` from the backend (no DB column on `core/models/review.py`), so the progress bar will sit at 0% and jump straight to the completed results. This is still better than a spinner but won't show real incremental progress until the backend is updated separately.
- `apiClient.getReviewStatus` in `frontend/src/services/api.ts` types its return as `Promise<Review>`, but the actual response shape from the status endpoint is `{ review_id, status, progress_pct }` — not a full `Review` object. Adding `progress_pct` to the `Review` type works around this, but a cleaner fix would be a dedicated `ReviewStatus` interface. Keeping `Review` avoids a larger refactor for now.
- The `useReviewStatus` hook in `frontend/src/hooks/useReviewStatus.ts` sets `isPolling` to `true` as initial state, meaning there is a brief flash of the loading UI on every page load even for already-completed reviews. This pre-exists the bug and is out of scope, but worth noting.

### Edge cases

- `progress_pct` is `undefined` (API response missing the field) — default to `0`
