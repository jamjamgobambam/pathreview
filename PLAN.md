## Solution plan

**Issue:** Add a "Copy link" button to share a public review summary
https://github.com/ascherj/pathreview/issues/101

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The feature has never been implemented. The root cause is a missing service layer, missing API endpoint, and missing database support for share tokens. The existing Share button in `ReviewPage.tsx` simply copies `window.location.href` to the clipboard, which is an authenticated URL — anyone who clicks it without an account is redirected to the login page.

The expected behavior is that clicking "Copy link" generates a time-limited, public URL containing a unique token. Any user who opens that URL (without logging in) should see a read-only view of the review summary. The token should expire after 30 days.

### Map
Which files, functions, or modules are involved?

- `frontend/src/pages/ReviewPage.tsx` — update the Share button's `handleShare` to call the share service instead of copying `window.location.href`
- `frontend/src/services/shareService.ts` — create this file; it does not currently exist; it will contain the function that calls the share API and returns the public link
- `api/routes/reviews.py` — add two new endpoints: `POST /reviews/{review_id}/share` (generates a token) and `GET /reviews/public/{token}` (public, no auth required)
- `core/models/share_token.py` — create a new `ShareToken` SQLAlchemy model with `id`, `token`, `review_id`, `expires_at`, and `created_at` fields
- `alembic/versions/` — add a migration to create the `share_tokens` table
- `api/schemas/share.py` — create Pydantic request/response schemas for the share endpoints

### Plan
What are the steps to fix this issue?

1. **Create the `ShareToken` database model** in `core/models/share_token.py` and write an Alembic migration to add the `share_tokens` table.
2. **Add backend endpoints** in `api/routes/reviews.py`: a protected `POST /reviews/{review_id}/share` route that generates a cryptographically random token (with a 30-day expiry) and stores it, plus a public `GET /reviews/public/{token}` route that looks up the token, checks expiry, and returns the read-only review data.
3. **Create `frontend/src/services/shareService.ts`** with a `generateShareLink(reviewId)` function that calls the `POST` endpoint and returns the full public URL.
4. **Update `frontend/src/pages/ReviewPage.tsx`** to replace the current `handleShare` function with one that calls `shareService.generateShareLink` and copies the returned URL to the clipboard.
5. **Test end-to-end**: generate a link while logged in, open it in an incognito window, and confirm it renders the review without authentication.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** A logged-in user clicks "Copy link" on their review page. The review ID is passed to the share API.
- **Output:** A unique public URL (e.g. `https://app/share/<token>`) is copied to the clipboard. Opening that URL without an account displays a read-only view of the review summary and expires after 30 days.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- The public `GET /reviews/public/{token}` endpoint must not require authentication, which means it bypasses the existing auth middleware. Care is needed to ensure it only exposes read-only data for the specific review tied to the token, and nothing else.
- Token expiry must be enforced server-side on every request, not just at generation time, to prevent access after the 30-day window.
- It is unclear from the issue whether the share page should be a new frontend route (`/share/:token`) or handled server-side. A new frontend route with a dedicated public page component is the most likely approach.

### Edge cases
What inputs or states should your fix handle gracefully?

- **Expired token:** Return a `410 Gone` or `404` response; the frontend should show a clear "This link has expired" message.
- **Invalid/non-existent token:** Return `404`.
- **Review still processing:** If the review has not completed, the share link should either be blocked until completion or display a "review is still being generated" state.
- **Multiple share requests:** Calling `POST /reviews/{review_id}/share` more than once should either return the existing active token or generate a new one and invalidate the old one. This decision should be consistent and documented.
