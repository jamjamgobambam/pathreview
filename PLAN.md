## Solution plan

**Issue:** [#101 - Add a "Copy link" button to share a public review summary](https://github.com/ascherj/pathreview/issues/101)

### Understand

**Root cause.** The "Share" button on the review page does not create a shareable resource, it
just copies the current browser URL to the clipboard:

```ts
// frontend/src/pages/ReviewPage.tsx:32-37
const handleShare = () => {
  const url = window.location.href            // e.g. http://localhost:5173/reviews/<id>
  navigator.clipboard.writeText(url).then(() => {
    alert('Review link copied to clipboard!')
  })
}
```

That URL points at `/reviews/:reviewId`, which is behind two independent auth gates:

1. **Route gate.** `/reviews/:reviewId` is wrapped in `ProtectedRoute`
   (`frontend/src/App.tsx:79-86`), which redirects any visitor without a session to `/login`
   (`App.tsx:25-27`).
2. **API gate.** `GET /reviews/{review_id}` depends on `get_current_user`
   (`api/routes/reviews.py:65-70`), and `get_review()` only returns the row when it joins to a
   profile owned by the requesting user (`core/services/review_service.py:35-47`). A stranger
   gets `401` (no token) or `404` (not their review).

**Expected vs. actual.**
- *Expected:* clicking Share produces a link that anyone can open (with no account and no login)
  to see a read-only copy of the review, and that link stops working after 30 days.
- *Actual:* the copied link only works for the logged-in owner in the same browser session.
  Opening it in an incognito window / another browser redirects to the login page and the review is
  never shown.

There is no share token, no public endpoint, and no public route anywhere in the codebase.

### Map

**Backend (Python / FastAPI + async SQLAlchemy)**
- `core/models/share_link.py`: a **new** `ShareLink` model holding `id`, `review_id` (FK ->
  `reviews.id`, `ondelete="CASCADE"`), `token` (unique, indexed), `expires_at`, and `created_at`.
- `core/models/__init__.py`: register `ShareLink` in the imports and `__all__` so
  `Base.metadata.create_all()` (called by `init_db()` on startup, `core/database.py:42-45`)
  creates the table. There is no Alembic in this repo, so table creation is import-driven.
- `core/services/share_service.py`: **new** service functions `create_share_link(db, review_id, user_id)`
  (owner check and token generation) and `get_review_by_share_token(db, token)` (token lookup and
  expiry check, no user scope).
- `api/routes/reviews.py`: add `POST /reviews/{review_id}/share` (authenticated, owner-only)
  and `GET /reviews/shared/{token}` (public, **no** `get_current_user` dependency).
- `api/schemas/review.py`: add `ShareLinkResponse` (`share_url`, `token`, `expires_at`) and
  `PublicReviewResponse` (the read-only view with `status`, `sections`, `overall_score`, and
  `created_at`, deliberately **omitting** `profile_id` and any owner data).

**Frontend (React + TypeScript + Vite)**
- `frontend/src/services/shareService.ts`: **new**. `createShareLink(reviewId)` calls the POST
  endpoint and returns the absolute share URL, plus a `copyToClipboard(url)` helper.
- `frontend/src/services/api.ts`: add `createShareLink(reviewId)` and `getSharedReview(token)`
  methods, mirroring the existing `apiClient` pattern.
- `frontend/src/components/ShareModal.tsx`: **new** modal component. Shows the generated share
  URL in a read-only text field with a **Copy** button that writes to the clipboard and flips to a
  "Copied" confirmation. Built with Tailwind (overlay + centered card) to match the existing
  button styling, replacing the native `alert()`.
- `frontend/src/pages/ReviewPage.tsx`: rewrite `handleShare` to call `shareService`, store the
  returned URL in state, and open `ShareModal` instead of copying and firing `alert()` (replacing
  the `window.location.href` logic at lines 32-37).
- `frontend/src/pages/SharedReviewPage.tsx`: **new** read-only page that fetches
  `GET /reviews/shared/:token` and renders score and `ReviewSection`s, with no NavBar actions and
  no "Back to Dashboard" button.
- `frontend/src/App.tsx`: add a **public** route `/shared/:token` mapped to `SharedReviewPage`,
  outside `ProtectedRoute`.
- `frontend/src/types/index.ts`: add `ShareLink` and `PublicReview` interfaces.

### Plan

1. **Data + service layer.** Add the `ShareLink` model, register it in
   `core/models/__init__.py`, and write `core/services/share_service.py`.
   `create_share_link` verifies the review belongs to `user_id` (reuse the join in
   `get_review`), generates a token with `secrets.token_urlsafe(32)`, and stores
   `expires_at = datetime.utcnow() + timedelta(days=30)`. If a non-expired link already exists,
   return it instead of minting a duplicate. Before minting a fresh link, delete any expired
   rows for that review (`expires_at < datetime.utcnow()`) so the table does not grow unbounded.
2. **API endpoints.** In `api/routes/reviews.py`, add `POST /reviews/{review_id}/share` (returns
   `ShareLinkResponse`, `404` if the caller doesn't own the review) and the **public**
   `GET /reviews/shared/{token}` (returns `PublicReviewResponse`, with `404` for an unknown token
   and `410 Gone` for an expired one). Add both schemas to `api/schemas/review.py`.
3. **Frontend service + share modal.** Add `apiClient.createShareLink` / `getSharedReview`, create
   `shareService.ts`, and build `ShareModal.tsx`. Update `ReviewPage.handleShare` to await the
   created link, store the URL in state, and open the modal (with a loading state while the POST is
   in flight and an error state if it fails, so the modal never shows an empty link). The modal's
   **Copy** button uses `shareService.copyToClipboard` and shows a "Copied" confirmation.
4. **Public view + route.** Build `SharedReviewPage.tsx` (loading / not-found / expired /
   success states) and register the unguarded `/shared/:token` route in `App.tsx`.
5. **Tests + manual verification.** Add a backend test that a fresh token resolves and an
   expired one returns `410`, plus a frontend test for `handleShare`. Manually verify by copying
   a link and opening it in an incognito window, where the review should render without login.

### Inputs & outputs

- **Input (generate):** a `review_id` and the authenticated owner's JWT.
  **Output:** `{ share_url, token, expires_at }`, and a persisted `share_links` row.
- **Input (view):** an opaque `token` from the URL, no auth.
  **Output:** a read-only `PublicReviewResponse` (score + sections), or `404`/`410`.
- **Net change:** one new DB table, two new API routes, one new public frontend route/page, and
  a rewired Share button.

### Risks & unknowns

- **Auth boundary leak.** The public endpoint must not reuse `get_current_user` or return
  `ReviewResponse` (which exposes `profile_id`). Risk lives in `api/routes/reviews.py` and the
  new `PublicReviewResponse` in `api/schemas/review.py`, where an over-broad schema would leak
  owner data. Mitigate by whitelisting fields, not blacklisting.
- **No migration tooling.** The repo has no Alembic. Tables come from `Base.metadata.create_all`
  at startup (`core/database.py:42-45`), which only creates *missing* tables and never alters
  existing ones. The new table appears on the next restart, but I'm unsure whether the Postgres
  volume in `docker compose` persists an old schema, so it may need a restart or a manual `CREATE`.
- **Token expiry only enforced in code.** Expiry is a `datetime` compared at request time, not a
  DB TTL, so old rows do not disappear on their own. `create_share_link` handles this by deleting
  a review's expired rows whenever a new link is generated, which keeps the table bounded without
  a scheduler. Tokens for reviews nobody ever re-shares still linger, which is acceptable at this
  scale.
- **Unknown: regenerate vs. reuse.** The issue doesn't say whether re-clicking Share should
  return the same link or mint a new one. Defaulting to "reuse if not expired", which needs
  confirmation.
- **Clipboard API.** `navigator.clipboard` requires a secure context. On `localhost` it's fine,
  but it can reject or be unavailable elsewhere. The `ShareModal` keeps the URL visible in a
  read-only field so the user can always select and copy manually even if the **Copy** button
  fails, and the button surfaces a failure state instead of silently doing nothing.

### Edge cases

- **Expired token** (> 30 days) -> `410 Gone`. `SharedReviewPage` shows a "link expired" message,
  not a spinner.
- **Invalid / malformed / tampered token** -> `404`, generic "not found" (no info leak about
  whether the review exists).
- **Review not yet complete** (`status` = `pending` / `processing` / `failed`) when a link is
  generated -> the public view should render the same status states as `ReviewPage`, not crash on
  missing `sections`.
- **Deleted review / profile.** FK `ondelete="CASCADE"` removes the `share_links` row, so the
  token 404s cleanly.
- **Owner clicks Share twice** -> returns the existing non-expired link (no duplicate rows).
- **Share link generation fails or is slow** -> the modal shows a loading state while the POST is
  in flight and an error message if it fails, never an empty or half-rendered link.
- **Copy button fails** (clipboard blocked) -> the URL stays visible in the read-only field for
  manual copy, and the button shows a failure state rather than a false "Copied" confirmation.
- **Anonymous user hits `/shared/:token`** -> renders normally (no redirect to `/login`), the
  whole point of the fix.
- **Non-owner calls the POST generate endpoint** -> `404` (mirrors existing `get_review`
  behavior, doesn't reveal the review exists).
