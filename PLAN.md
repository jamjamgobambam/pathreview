## Solution plan

**Issue:** Add a "Copy link" button to share a public review summary #101 — https://github.com/ascherj/pathreview/issues/101

### Understand

The "Share" button on `ReviewPage.tsx` already exists and copies a link to the clipboard, so on the surface the feature looks implemented. The actual bug is that it copies `window.location.href` — the private, authenticated review URL. That route (`GET /reviews/{review_id}`) requires `get_current_user` and filters by `user_id=current_user.id`, so anyone other than the owner hits a login wall or a 404. Expected behavior: the copied link should open a read-only view of the review with no login required, and stop working after 30 days. Actual behavior: the link only works for the logged-in owner and never expires, because no separate public/token-based access path exists.

### Map

- `frontend/src/pages/ReviewPage.tsx` — `handleShare()` needs to request a share link instead of copying the current URL
- `frontend/src/services/api.ts` — add `createShareLink(reviewId)` and `getSharedReview(token)` methods (no separate `shareService.ts` exists; this repo keeps all API calls in one `ApiClient`)
- `api/routes/reviews.py` — add a `POST /reviews/{review_id}/share` (authenticated) endpoint and a `GET /reviews/shared/{token}` (public) endpoint
- `core/models/` — new model for share tokens (e.g. `ShareLink`) with `token`, `review_id`, `created_at`, `expires_at`
- `core/services/review_service.py` — helper functions for creating/validating share tokens, following the existing pattern of `create_review`/`get_review`
- A new frontend route/page (e.g. `/shared/:token`) to render the read-only view for logged-out visitors

### Plan

1. Add a `ShareLink` model/table (token, review_id, created_at, expires_at) and a DB migration
2. Add `POST /reviews/{review_id}/share` to generate and persist a token, returning the shareable URL
3. Add `GET /reviews/shared/{token}` as a public endpoint (no auth dependency) that validates expiry and returns a read-only review payload
4. Update `api.ts` with `createShareLink` and `getSharedReview`, and fix `handleShare()` in `ReviewPage.tsx` to call `createShareLink` before copying to clipboard
5. Build a new public-facing page/route for `/shared/:token` that reuses `ReviewSection` but strips out owner-only actions (Share, Export, Back to Dashboard)

### Inputs & outputs

- **Input:** a `review_id` (from an authenticated request) to generate a share link; a `token` (from an unauthenticated request) to fetch the shared view
- **Output:** a shareable URL containing the token; a read-only review payload (or a 404/410 if the token is invalid or expired)

### Risks & unknowns

- Token generation needs to be cryptographically random/unguessable to prevent enumeration — need to confirm what random/UUID utility the codebase already uses elsewhere
- Unsure whether expired tokens should be actively deleted (cron/background job) or just checked lazily on access — leaning toward lazy check for now, but worth confirming with maintainers
- Need to check whether the read-only payload should omit any fields (e.g. internal scores, PII) before returning it publicly
- Haven't confirmed the exact routing/auth pattern FastAPI expects for a route with no `Depends(get_current_user)` alongside other routes that require it in the same router

### Edge cases

- Token doesn't exist (typo'd or tampered link) → 404
- Token exists but is past `expires_at` → 404 or 410 Gone, not a silent/broken page
- Review is still in `pending`/`failed` status when someone visits the shared link → handle gracefully, not just assume `complete`
- Owner regenerates a share link — should the old token still work, or get invalidated?
- Owner deletes their profile/review after a share link was already sent out
