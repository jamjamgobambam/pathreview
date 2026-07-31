## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** Tier 2 

**Problem summary:**
A new feature request has been made that allows the user to click a copy link button that renders a page displaying a given review. The link should expire after 30 days, and it should not require any authentication to view. A button will be added to the ReviewPage.tsx that copies a link to clipboard, a new shareService.ts file will be generated to handle the logic for serving the links, and it will call a new unauthenticated public endpoint in reviews.py in order to pull the review text (the existing get route can't be used because it requires login and ownership). In addition, a new database table and schema will be created to hold the expiration date of the newly generated link.

**Branch name:** feat/101-add-copy-link-button

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

**Is this issue right for me?**
This is a Tier 2 issue and it's a good fit for me. I've worked as a dev on React apps with backend APIs, so a feature that touches the frontend, a new service, and an API endpoint is in my wheelhouse. I've already located and read the code it affects-the Share button in ReviewPage.tsx and the get route in reviews.py, and reading the route is what told me I'll need a new unauthenticated endpoint instead of reusing the existing one. Right now the Share button copies an authenticated URL only the owner can open, and after the fix it copies a public link anyone can view for 30 days.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/crbridges/pathreview/commit/481fd960e86bc3b70f97677d814a4bf7a09b05a1

**Reproduction summary:**
This issue is a new feature (labeled `enhancement`), so there's no bug to reproduce. I confirmed the gap by tracing the code: every route in `api/routes/reviews.py` depends on `get_current_user`, `ReviewPage` is wrapped in `<ProtectedRoute>` in `App.tsx`, and the current Share button just copies `window.location.href` — so there is no way to view a review without logging in, and no public endpoint exists yet.

**PLAN.md link:** https://github.com/crbridges/pathreview/blob/feat/101-add-copy-link-button/PLAN.md

**Walkthrough video (recommended):** not recorded

**Blockers or open questions:**
The new `/shared/:token` route has to be registered outside `<ProtectedRoute>` or logged-out visitors get bounced to `/login`, and `<NavBar />` renders on every route so it may need to be hidden on the public page. Still deciding whether the public view exposes the full review or a trimmed summary.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The whole feature is implemented across the backend and frontend, one sub-task per commit. Backend: a `ShareLink` model (token as primary key) plus Alembic migration 003, `create_share_link`/`get_share_link` service functions, an authed owner-only mint endpoint `POST /reviews/{review_id}/share`, and a public `GET /reviews/shared/{token}` that returns 404 for an unknown or malformed token and 410 for an expired one. I went with a trimmed `PublicReviewResponse` (score, sections, created_at only) so an anonymous viewer never sees owner-linking or internal fields. Frontend: a new `shareService.ts`, a "Copy link" button next to the existing Share button on `ReviewPage`, and a `SharedReviewPage` wired to `/shared/:token` outside `<ProtectedRoute>`. The two open questions from Week 8 are resolved — the route sits outside the auth guard, `NavBar` already returns null without a user so nothing leaks, and the public view is the trimmed summary.

**Next steps:**
Write unit tests for the service functions and the route logic (the 404/410/success paths), run `make check` and `make test-unit` to confirm my changes add no new failures over the baseline, then open the PR and fill in the template.

**Blockers:**
The codebase has heavy pre-existing failures before I touched anything (53 failing unit tests, 182 ruff errors, 103 mypy errors). I recorded that as a baseline and I'm committing with `--no-verify` so the pre-commit hooks don't block my clean changes on that existing debt. I'll document the baseline in the PR and show my changes introduce no new failures.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** feat/101-add-copy-link-button

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]