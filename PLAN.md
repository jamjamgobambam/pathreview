# PLAN.md — Issue #101: "Copy link" button for a public review summary

**Issue:** https://github.com/ascherj/pathreview/issues/101
**Branch:** `feat/101-share-review-link`
**Tier:** 2
**Author:** LaxmiPrasanna Ravikanti

---

## 1. Goal

Add a "Copy link" button to the review page that generates a **public, read-only,
30-day-expiring** link to a completed review summary. Anyone with the link can open it
**without logging in**; after 30 days the link stops working.

## 2. Current behavior (reproduction)

On the review page the "Share" button already exists but is a placeholder — it copies the
**current authenticated URL** and pops a browser `alert`:

```tsx
// frontend/src/pages/ReviewPage.tsx:32-37
const handleShare = () => {
  const url = window.location.href
  navigator.clipboard.writeText(url).then(() => {
    alert('Review link copied to clipboard!')
  })
}
```

To reproduce the gap:
1. `make run`, log in, open a completed review at `/reviews/:reviewId`.
2. Click **Share** → it copies `http://localhost:5173/reviews/:reviewId`.
3. Open that URL in a logged-out/incognito browser → `ProtectedRoute`
   (`frontend/src/App.tsx:12-30`) redirects to `/login`. The summary is **not**
   viewable without an account.

So the current link is not shareable with anyone who lacks an account. That is the
problem #101 asks us to fix.

## 3. Design decisions

| Decision | Choice | Why / alternatives |
|---|---|---|
| Link identifier | Opaque **share token** (`secrets.token_urlsafe(32)`) stored in a new `share_links` table | Unguessable; does not leak the internal `review_id`. Alternative (signed JWT with 30d `exp`) avoids a table but can't be revoked and bloats the URL. A DB row lets us enforce/rescind server-side. |
| Expiry enforcement | `expires_at` column checked **server-side** on every public read | The 30-day rule must live on the backend, not just be hidden in the UI. `created_at + timedelta(days=30)`. |
| Public endpoint auth | A route with **no `get_current_user` dependency** | Auth in this app is per-route DI (`api/middleware/auth.py`), not global middleware, so omitting the dependency makes a route public — the pattern `api/routes/health.py` already uses. |
| Public response shape | New `SharedReviewResponse` schema = summary fields only (`overall_score`, `sections`, `created_at`), **no** `profile_id`/owner linkage | Share the summary, not ownership metadata. Minimizes what a public link exposes. |
| Shareable state | Only `status == "complete"` reviews can be shared | A pending/failed review has no summary to show. |
| Not-found vs expired | Return **404** for both invalid and expired tokens | Avoids leaking whether a token ever existed (enumeration). The frontend shows one friendly "This link is no longer available" message. *(Open question — see §8; 410 Gone is the alternative if maintainers prefer distinguishing expired.)* |
| One link per review? | On create, **reuse an existing non-expired link** if present; otherwise mint a new one | Avoids unbounded row growth and gives a stable URL. Alternative (always mint new) is simpler but proliferates tokens. |

## 4. Data model & API contract

### New table `share_links` (migration `alembic/versions/003_add_share_links.py`)

| column | type | notes |
|---|---|---|
| `id` | `UUID(as_uuid=False)` string PK | mirrors `reviews.id` style (`core/models/review.py:22-24`) |
| `review_id` | FK → `reviews.id`, `ondelete=CASCADE` | deleting a review removes its links |
| `token` | `String`, **unique + indexed** | the value in the public URL |
| `created_at` | `DateTime(timezone=True)` | |
| `expires_at` | `DateTime(timezone=True)` | `created_at + 30 days` |

Migration mirrors the `001_initial_schema.py` `op.create_table` style; `revision="003"`,
`down_revision="002"`.

### Endpoints

```
POST /reviews/{review_id}/share      (auth required — must own the review)
  → 201 { token, share_url, expires_at }
  → 404 if review not owned / not found
  → 409 (or 400) if review not complete

GET  /share/{token}                  (PUBLIC — no auth)
  → 200 SharedReviewResponse { overall_score, sections, created_at, expires_at }
  → 404 if token invalid OR expired
```

Route ordering note: `GET /share/{token}` lives in a **new** public router
`api/routes/share.py` (prefix `/share`), so it never collides with the auth'd
`GET /reviews/{review_id}`.

## 5. Implementation steps (by layer)

### Backend
1. **Model** — `core/models/share_link.py`: `ShareLink` SQLAlchemy model (above schema).
   Register it in `core/models/__init__.py` (`import` + `__all__`) — alembic autogenerate
   and `Base.metadata` depend on this.
2. **Migration** — `alembic/versions/003_add_share_links.py`; verify with
   `make migrate` then `alembic downgrade -1` / `upgrade head` round-trip.
3. **Schemas** — `api/schemas/review.py`: add `ShareLinkResponse` (token, share_url,
   expires_at) and `SharedReviewResponse` (summary subset, `model_config =
   {"from_attributes": True}`).
4. **Service** — `core/services/share_service.py` (mirrors `review_service.py` async
   `select(...) / await db.execute / .scalars().first()` style):
   - `create_share_link(db, review_id, user_id)` — verify ownership by joining `Profile`
     (same filter as `get_review`), guard `status == complete`, reuse/mint token, return row.
   - `get_shared_review(db, token)` — look up by token; return `None` if missing or
     `expires_at < now`; else return the joined `Review`.
5. **Routes** — `POST /reviews/{review_id}/share` in `api/routes/reviews.py` (auth'd,
   mirrors existing try/except + `HTTPException` + `structlog` pattern); new
   `api/routes/share.py` for public `GET /share/{token}`; register the new router in
   `api/main.py` (import + `include_router`).

### Frontend
6. **Types** — `frontend/src/types/index.ts`: `ShareLink` and `SharedReview` interfaces.
7. **API client** — `frontend/src/services/api.ts`: `createShareLink(reviewId)` (POST) and
   `getSharedReview(token)` (GET; works logged-out since `getAuthHeader()` returns `{}`
   with no token).
8. **Copy-link button** — replace `handleShare` in `ReviewPage.tsx:32-37`: call
   `createShareLink`, build `${window.location.origin}/share/${token}`, copy it, and show an
   inline **"Copied!"** confirmation (local `useState` + `Check` icon from `lucide-react`,
   reset after ~2s) instead of `alert`. Reuse the existing button classes (`ReviewPage.tsx:116`).
9. **Public share page** — new `frontend/src/pages/SharePage.tsx`: read `:token`, call
   `getSharedReview`, render read-only summary by **reusing `ReviewSection`**; show the
   existing red error-banner style (`ReviewPage.tsx:83-85`) on 404/expired.
10. **Route** — `frontend/src/App.tsx`: add `<Route path="/share/:token"
    element={<SharePage />} />` **outside** `ProtectedRoute` (next to `/login`, `/register`).
    `NavBar` already renders `null` when logged out, so the shared view shows no nav.

## 6. Test plan

Focus (per my own scope note in JOURNAL): **token creation and expiry**.

**Backend** — `tests/unit/test_share_service.py`, mirroring `tests/unit/test_review_service.py`
(`@pytest.mark.unit`, `@pytest.mark.asyncio`, mocked `AsyncMock` session, `patch` the model):
- create returns a token and `expires_at ≈ now + 30d`;
- create on a review the user doesn't own → `None`/raises (no leak);
- create on a non-complete review → guarded error;
- `get_shared_review` with a valid, unexpired token → returns the review;
- `get_shared_review` with an **expired** token → `None`;
- `get_shared_review` with an unknown token → `None`.

**Frontend** (vitest, mirror `frontend/src/components/__tests__/ProfileForm.test.tsx`
`vi.mock` of the api client):
- `SharePage` renders sections when `getSharedReview` resolves; shows the error banner when
  it rejects (expired/invalid).
- `ReviewPage` share button calls `createShareLink`, writes the returned URL to
  `navigator.clipboard`, and shows the "Copied!" confirmation.

*Note:* there is no route/integration client fixture in this repo yet
(`tests/integration/` is empty), and `make test-unit` only runs `tests/unit -m unit`. I'll
keep the graded tests as unit tests in that path. A `httpx.AsyncClient` route test is a
possible stretch but is **out of scope** to avoid introducing new test infrastructure.

## 7. Pre-PR checks (contribution standards)

- `make check` — ruff + **black (reformats in place → commit the result)** + mypy.
  New backend code must be fully type-annotated (`disallow_untyped_defs = true`,
  line-length 100).
- `make test-unit`
- `cd frontend && npm test && npm run build` (tsc typecheck via build; no Makefile target).
- Google-style docstrings on new public functions/classes (CONTRIBUTING §Code Style).
- Conventional commits, scopes `api` / `frontend`. Planned sequence:
  - `feat(api): add share_links model and migration`
  - `feat(api): add public share endpoint and share service`
  - `feat(frontend): add copy-link button and public share page`
  - `test(api): add share service unit tests` / `test(frontend): add share page + button tests`
  - `docs(api): document share endpoints in docs/API.md`
- Fill out the PR template completely; `Fixes #101`.

## 8. Open questions for maintainers

1. **Expired vs invalid** — is 404-for-both acceptable, or do you want **410 Gone** for
   expired so the UI can say "expired" specifically? (I lean 404 to avoid enumeration.)
2. **One active link per review**, reused on repeat clicks — is that the desired behavior,
   or mint a fresh token each time?
3. Should creating a share link be **rate-limited**? (The app has rate limiting per
   ARCHITECTURE.md; unclear if it applies here.)

## 9. Out of scope

Link **revocation UI**, share **analytics**, custom expiry windows, password-protected
links, and CORS changes (shared links are opened same-origin at `/share`, so
`api/main.py` CORS config needs no change).
