## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/101)

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
There is currently no way for a user to share their review summary with someone who 
doesn't have an account. This issue asks for a shareable link that renders a read-only 
version of the review page without requiring login, and that link should stop working 
after 30 days. It touches ReviewPage.tsx and a new shareService.ts on the frontend, 
and the reviews API route on the backend. So it needs a new endpoint to generate/store 
a share token, a public endpoint to serve the shared view, and a UI entry point 
(the copy-link button) to trigger it.

**Branch name:** feat/101-shareable-review-link

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
`https://github.com/ascherj/pathreview/commit/92a94d9997dafe23f66b49e60dec9ec8056b9296`

**Reproduction summary:**
Ran the app locally (`make run`), opened a completed review, and clicked **Share**. The button
copies the current tab URL (`http://localhost:5173/reviews/<id>`). Opening that link in an
incognito window redirected straight to `/login` instead of showing the review, confirming the
"shared" link is auth-gated and useless to anyone without an account.

**Where it lives (code-level confirmation):**
- `frontend/src/pages/ReviewPage.tsx:32-37` - `handleShare` just copies `window.location.href`;
  it never creates a shareable resource.
- `frontend/src/App.tsx:79-86` - `/reviews/:reviewId` is wrapped in `ProtectedRoute`, which
  redirects anonymous visitors to `/login` (`App.tsx:25-27`).
- `api/routes/reviews.py:65-70` + `core/services/review_service.py:35-47` - `GET /reviews/{id}`
  requires `get_current_user` and only returns reviews owned by the caller, so a stranger gets
  `401`/`404` even if they reach the route.

**PLAN.md link:** [PLAN.md](https://github.com/KaKitLeng/pathreview/blob/feat/101-shareable-review-link/PLAN.md)

**Walkthrough video (recommended):** [Recording](https://www.loom.com/share/7b99653a61a440d0a878137f72da2fb9)

**Blockers or open questions:**
- No Alembic in the repo — new tables come from `Base.metadata.create_all` at startup. Need to
  confirm the Postgres volume in `docker compose` picks up the new `share_links` table on
  restart rather than needing a manual create.
- Should re-clicking Share reuse the existing (non-expired) link or mint a new token each time?
  Planning to reuse, will confirm with a mentor.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The whole backend is implemented and verified against my local Postgres. Sub-tasks from PLAN.md
that are done:
- **Data layer:** `ShareLink` model (`core/models/share_link.py`) with `token`, `expires_at`, and a
  `review_id` FK (`ondelete="CASCADE"`), registered in `core/models/__init__.py` with a
  `Review.share_links` relationship.
- **Database:** the repo actually uses Alembic (not `create_all` at startup, as I assumed in
  Week 8), so I added migration `003_add_share_links.py` and applied it. The DB is now at
  revision `003` with the `share_links` table live.
- **Service layer:** `core/services/share_service.py`, with `create_share_link` (owner check,
  reuses a non-expired link instead of duplicating, deletes expired rows before minting) and
  `get_review_by_share_token` (public lookup, raises `ShareLinkExpiredError` on expiry).
- **API:** `POST /reviews/{review_id}/share` (authenticated, owner-only, 404 if not owned) and the
  public `GET /reviews/shared/{token}` (404 unknown, 410 expired) in `api/routes/reviews.py`.
- **Schemas:** `ShareLinkResponse` and `PublicReviewResponse`, which whitelists fields so no
  `profile_id`/owner data leaks through the public view.
- **Tests:** `tests/unit/test_share_service.py` with 10 unit tests (token reuse, expiry, ownership,
  token generation), all passing. Confirmed `make check` and `make test-unit` introduce no new
  failures against the pre-existing baseline (385 passed, same 53 pre-existing failures).

Both Week 8 open questions are resolved. The repo does use Alembic (migration added), and
re-clicking Share reuses the existing non-expired link (implemented and tested).

**Next steps:**
- Build the frontend: `shareService.ts` and `apiClient` methods, a `ShareModal` component, rewire
  `ReviewPage.handleShare`, and a read-only `SharedReviewPage` on an unguarded `/shared/:token`
  route in `App.tsx`.
- Manually verify end-to-end by copying a link and opening it in an incognito window (should render
  read-only, no login), then open a draft PR for peer/mentor review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/678

**Branch:** `feat/101-shareable-review-link`

**What you built:**
A shareable review link. The owner clicks Share to generate a tokenized link that expires after 30
days, and anyone can open `/shared/:token` to see a read-only, whitelisted view of the review with
no account and no login. The backend adds a `ShareLink` model, an Alembic migration, a share
service, and owner-only plus public endpoints. The frontend replaces the old clipboard-copy Share
button with a modal and adds a public `SharedReviewPage` on an unguarded route.

**Tests added or updated:**
- `tests/unit/test_share_service.py` (10 backend unit tests): link reuse on repeat Share, expiry
  raising `ShareLinkExpiredError`, a non-owner returning `None`, expired-row cleanup before minting,
  and token generation.
- `frontend/src/components/__tests__/ShareModal.test.tsx` (7 tests): loading and error states, the
  read-only URL field, Copy flipping to "Copied", and the copy-failure fallback.

**Self-review confirmation:** 
- [x] make check passes  
- [x] make test-unit passes

Pre-existing failures documented: on the branch base (my changes stashed), `make test-unit` reports
53 failed / 375 passed and `make check` reports ruff and mypy errors across unrelated modules (for
example `core/services/review_service.py`, skill extraction, tech detection). My changes introduce
no new failures. With my changes `make test-unit` is 53 failed / 385 passed (my 10 new tests pass),
ruff drops from 182 to 161, black improves by one file, and my new files are ruff, black, and mypy
clean. Per the Week 9 guidance, "passes" here means my changes add no new failures. The frontend
tests pass separately via `npm test` (7 of 7).

**Draft PR feedback received from:** none

