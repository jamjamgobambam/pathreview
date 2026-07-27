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


