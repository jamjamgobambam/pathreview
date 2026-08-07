# PLAN.md — Issue #101: Copy link to share a public review summary

***Issue link:*** https://github.com/ascherj/pathreview/issues/101
***Branch:*** feat/101-copy-link-public-review-summary

## 1. Understand

**Root cause:** [ReviewPage.tsx:32-37](frontend/src/pages/ReviewPage.tsx#L32-L37) implements `handleShare()` by copying `window.location.href` — the currently-loaded authenticated URL (`/reviews/{reviewId}`). This URL resolves to a `ProtectedRoute` in [App.tsx:79-86](frontend/src/App.tsx#L79-L86), which redirects unauthenticated visitors to `/login` ([App.tsx:25-27](frontend/src/App.tsx#L25-L27)). The underlying data fetch, `GET /reviews/{review_id}` in [reviews.py:65-98](api/routes/reviews.py#L65-L98), also requires `current_user: User = Depends(get_current_user)`. There is no token-based mechanism anywhere in the stack for granting time-limited, unauthenticated read access to a review.

**Actual behavior:** Clicking "Share" copies a login-gated URL. Anyone without valid session credentials who opens it is redirected to the login page and cannot view the review.

**Expected behavior:** Clicking "Share" (or a renamed "Copy link" action) generates a unique, unguessable share token tied to that review, copies a public URL containing that token (e.g. `/shared-review/{token}`), and that URL renders a read-only summary for 30 days from creation — with no login required and no ability to edit/export/re-share from the public view.

## 2. Map — files to modify/create

**Backend**
- `core/models/review_share.py` *(new)* — `ReviewShare` SQLAlchemy model
- `core/models/__init__.py` — register new model
- `alembic/versions/003_add_review_shares.py` *(new)* — migration for `review_shares` table
- `core/services/review_service.py` — add `create_share_token()`, `get_review_by_share_token()`
- `api/schemas/review.py` — add `ShareCreateResponse`, `SharedReviewResponse` schemas
- `api/routes/reviews.py` — add `POST /reviews/{review_id}/share` (authenticated) and `GET /reviews/shared/{share_token}` (public)

**Frontend**
- `frontend/src/services/shareService.ts` *(new)* — calls the share-generation endpoint, returns the public URL
- `frontend/src/pages/ReviewPage.tsx` — replace `handleShare()` body to call `shareService`, copy the returned public URL
- `frontend/src/pages/SharedReviewPage.tsx` *(new)* — read-only page for the public route
- `frontend/src/App.tsx` — add unauthenticated route `/shared-review/:shareToken` (outside `ProtectedRoute`)
- `frontend/src/services/api.ts` — add `createShareLink()` and `getSharedReview()` methods
- `frontend/src/types.ts` (or wherever `Review` types live) — add `ShareResponse` type

## 3. Plan

1. **Data layer:** Add `ReviewShare` model + Alembic migration (`share_token` unique/indexed, `review_id` FK, `created_at`, `expires_at`).
2. **Backend endpoints:** Implement `POST /reviews/{review_id}/share` (auth required; generates token, sets `expires_at = now + 30 days`, returns public URL) and `GET /reviews/shared/{share_token}` (no auth; validates existence + expiry, returns a trimmed read-only payload).
3. **Frontend service:** Build `shareService.ts` wrapping the new API calls; update `ReviewPage.tsx`'s `handleShare()` to call it and copy the returned link instead of `window.location.href`.
4. **Public view:** Add `SharedReviewPage.tsx` + unauthenticated route to render the shared, read-only payload (no Share/Export buttons, no nav requiring auth).
5. **Verify end-to-end:** Manually reproduce the original bug is fixed — generate a link, open in incognito, confirm it loads without login; confirm an expired/invalid token returns a clear error instead of a login redirect.

**Detailed, step-by-step build order (data layer → routes → frontend → verification, one commit per step) lives in [IMPLEMENTATION_STEPS.md](IMPLEMENTATION_STEPS.md).** This section stays as the high-level plan; that file is the executable roadmap this plan was carried out with, including the checkpoint and commit for each step.

## 4. Inputs & outputs

**`POST /reviews/{review_id}/share`** (authenticated)
- Path param: `review_id: UUID`
- Body: none
- Response 200:
  ```json
  {
    "share_token": "6f1a9c2e-...-b3",
    "share_url": "/shared-review/6f1a9c2e-...-b3",
    "expires_at": "2026-08-22T00:00:00Z"
  }
  ```
- Errors: 404 if review not found/not owned by user; 409 if review status != "complete" (can't share an in-progress review, TBD whether to allow)

**`GET /reviews/shared/{share_token}`** (public, no auth)
- Path param: `share_token: str`
- Response 200 (subset of `ReviewResponse` — no `profile_id`, no owner info):
  ```json
  {
    "sections": [...],
    "overall_score": 0.82,
    "created_at": "2026-07-23T00:00:00Z"
  }
  ```
- Errors: 404 for unknown token; 410 Gone for expired token

**Frontend `shareService.ts`**
- `generateShareLink(reviewId: string): Promise<{ shareUrl: string; expiresAt: string }>`
- `getSharedReview(token: string): Promise<SharedReview>`

**`ReviewPage.tsx` `handleShare()`**
- Input: current `reviewId` from route params
- Output: full absolute URL copied to clipboard (e.g. `${window.location.origin}/shared-review/{token}`), success/error toast

## 5. Risks & unknowns

- **Token guessability:** must use a cryptographically random token (e.g. `secrets.token_urlsafe(32)` or UUID4), not a sequential or predictable ID — treat it as a bearer credential.
- **Data leakage via public payload:** the public schema must exclude PII (owner email, profile details, internal IDs) — needs a dedicated `SharedReviewResponse` schema, not reuse of `ReviewResponse`.
- **Expiration enforcement location:** must be checked server-side on every fetch (not just at generation time) — comparing `expires_at` against current UTC time on each `GET /reviews/shared/{token}` call.
- **Schema migration:** new `review_shares` table needs a migration (`alembic revision`); must confirm FK `ondelete` behavior when a review or profile is deleted (cascade vs. orphaned share).
- **Re-sharing/regeneration:** unclear if calling `POST .../share` again should return the existing active token or always mint a new one (invalidating the old link). Needs a product decision — default assumption: return existing unexpired token if one exists, to avoid link-churn for users who re-click Share.
- **Rate limiting:** no current rate limiting on token generation; a malicious authenticated user could spam-generate tokens. Low risk for MVP but worth a TODO.
- **Clock/timezone handling:** `expires_at` must be stored and compared in UTC consistently (existing `Review.created_at` uses `datetime.utcnow`, should follow same convention).

## 6. Edge cases

- **Invalid/malformed token:** `GET /reviews/shared/{token}` returns 404 with a generic "Share link not found" message (don't leak whether the review exists).
- **Expired token:** return 410 Gone (or 404, kept generic) with a "This link has expired" message; frontend `SharedReviewPage` shows a friendly expired-state UI rather than a raw error.
- **Review deleted after share created:** FK cascade (`ondelete="CASCADE"` on `review_id`) removes the share row automatically; public endpoint then returns 404 same as invalid token.
- **Review not yet complete (status pending/processing/failed):** decide whether to block share-link generation until `status == "complete"`; recommend blocking with a 409 from the generate endpoint, and the frontend should hide/disable the Share button until the review is complete (already implicitly true since the button only renders inside the `fullReview.status === 'complete'` block, [ReviewPage.tsx:109-129](frontend/src/pages/ReviewPage.tsx#L109-L129)).
- **Unauthenticated access to public route:** `/shared-review/:token` must NOT be wrapped in `ProtectedRoute`; verify no global auth guard/interceptor in `api.ts` forces a redirect on 401 for this specific call path.
- **User tries to share someone else's review:** `POST /reviews/{review_id}/share` must verify `current_user.id` owns the review (mirror the ownership check already in `get_review()`), returning 404 (not 403, to avoid confirming existence) if not owned.
- **Multiple share links per review:** decide if only one active token is allowed at a time or multiple concurrent tokens are permitted; simplest MVP: one active token per review, regenerate returns the same one until expiry.
