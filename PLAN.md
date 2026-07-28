## Solution plan

**Issue:** [Add a "Copy link" button to share a public review summary](https://github.com/ascherj/pathreview/issues/101)

### Understand

This is a new feature (labeled `enhancement`), not a bug — there is no broken
behavior to reproduce. Today a review can only be viewed by its authenticated
owner: `GET /reviews/{review_id}` in `api/routes/reviews.py` depends on
`get_current_user` and filters by `user_id`, and the frontend `ReviewPage` is
wrapped in `<ProtectedRoute>` (redirects to `/login` when there is no session).
The existing "Share" button copies `window.location.href`, which points at that
authenticated page, so a logged-out recipient cannot open it.

**Expected after the fix:** the owner clicks a new "Copy link" button and gets a
public URL to a read-only view of the review. Anyone can open it without logging
in, and it stops working 30 days after it was created. The existing Share button
is left unchanged (out of scope for this enhancement).

### Map

Files I expect to touch:

**Backend**
- `core/models/share_link.py` *(new)* — SQLAlchemy model: `token`, `review_id` (FK), `expires_at`, `created_at`.
- `core/models/__init__.py` — import the new model so metadata/Alembic sees it.
- `alembic/versions/003_add_share_links.py` *(new)* — migration creating the table (follows `001`/`002`).
- `core/services/review_service.py` — add `create_share_link(review_id)` and `get_review_by_share_token(token)`.
- `api/schemas/share.py` *(new)* — Pydantic response schemas (mint result + public read-only view).
- `api/routes/reviews.py` — add `POST /reviews/{review_id}/share` (authed) and `GET /reviews/shared/{token}` (public).

**Frontend**
- `frontend/src/services/shareService.ts` *(new)* — `mintShareLink(reviewId)`, `getSharedReview(token)`.
- `frontend/src/pages/ReviewPage.tsx` — new "Copy link" button next to Share.
- `frontend/src/pages/SharedReviewPage.tsx` *(new)* — public read-only view.
- `frontend/src/App.tsx` — register `/shared/:token` **outside** `<ProtectedRoute>`.
- `frontend/src/types.ts` — types for the share responses.

### Plan

1. **Data layer** — add the `ShareLink` model + Alembic migration `003`, and the two
   service functions (`create_share_link`, `get_review_by_share_token`).
2. **Mint endpoint** — `POST /reviews/{review_id}/share` (keeps `get_current_user`,
   owner-only): create a token with `expires_at = now + 30 days`, return token/URL.
3. **Public endpoint** — `GET /reviews/shared/{token}` (no auth dependency): look up
   the token, reject if missing/expired, return the read-only review schema.
4. **Frontend service + button** — `shareService.ts` calling the mint endpoint;
   wire a new "Copy link" button in `ReviewPage.tsx` that copies the returned URL.
5. **Public view page + route** — `SharedReviewPage.tsx` that fetches by token and
   renders read-only; register `/shared/:token` outside the auth guard.

### Inputs & outputs

- **Mint:** input = `review_id` (owner authenticated). Output = a new `share_links`
  row and a public URL like `/shared/<token>`.
- **Public view:** input = `token` from the URL (no auth). Output = the review's
  read-only summary as JSON, or a 404/410 if the token is unknown or expired.
- **UI:** input = a click on "Copy link". Output = the public URL on the clipboard.

### Risks & unknowns

- **Auth-guard escape (frontend):** `/shared/:token` must be registered outside
  `<ProtectedRoute>` in `App.tsx`, or logged-out visitors get bounced to `/login`.
- **NavBar leakage:** `<NavBar />` renders on every route in `App.tsx` and shows
  logout/dashboard links a public visitor shouldn't see — may need to hide it on
  the shared page.
- **Auth-header assumption:** `apiClient.request()` always attaches the bearer
  token; the public GET must not depend on a token being present, which is why
  `shareService.ts` is separate.
- **Field exposure:** the issue says "review *summary*"; unsure whether to expose
  the full review shape or a trimmed subset — leaning trimmed to avoid leaking
  more than intended.

### Edge cases

- Unknown or malformed/non-UUID token in the URL → 404, never a 500.
- Token that exists but is past `expires_at` → 410 (or 404), not the review.
