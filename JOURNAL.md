## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Selection reasoning** I chose this Tier 2 issue because I've worked with React before but haven't implemented shareable URL patterns or public token-based access. Before claiming it, I located the relevant files — `frontend/src/pages/ReviewPage.tsx` for the button and `api/routes/reviews.py` for the backend access change — and confirmed the existing Share button stub is already there. There are no open blockers listed on the issue. I estimate 8–10 hours of work across Weeks 8–9, which fits my schedule.

**Problem summary:**

Right now, completed review summaries in PathReview can only be viewed by the person who generated them, there's no way to share a review with someone else, like a mentor or recruiter. The app is missing a "Copy link" button that would generate a publicly accessible URL for a given review and copy it to the clipboard. A successful fix would add this button to the review detail view in the frontend (ReviewPage.tsx), and likely requires a backend change to support unauthenticated access to a review by a public share token or ID that expires in 30 days.

**Branch name:** feat/101-copy-link-button

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tomisin05/pathreview/commit/1551889

**Reproduction summary:**
I confirmed the issue two ways. First, I opened the live app at `http://localhost:5173` and navigated to a completed review page. The top-right action area shows exactly two buttons: "Share" (with a share icon) and "Export" (blue button with a download icon). There is no "Copy link" button anywhere on the page. Second, I ran `npx vitest run src/pages/__tests__/ReviewPage.test.tsx` — both tests failed with `Unable to find role="button" and name /copy link/i`, and the DOM printed in the failure output matched what I saw in the browser: only the "Share" and "Export" buttons rendered. The feature is confirmed missing from both the live UI and the test environment.

**PLAN.md link:** https://github.com/tomisin05/pathreview/blob/feat/101-copy-link-button/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
The issue title says "public review summary" — it's unclear whether the link should be accessible without authentication. The current `GET /reviews/{review_id}` endpoint in `api/routes/reviews.py` requires a logged-in user. I'm implementing the frontend-only version first (copy the current URL) and will flag this in the PR for maintainer input.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are complete. Replaced the Share button in `ReviewPage.tsx` with a "Copy link" button that calls a new `POST /reviews/{review_id}/share` endpoint, receives a 30-day share token, copies the resulting public URL to the clipboard, and shows inline "Copied!" feedback for 2 seconds. Added `share_token` and `share_expires_at` columns to the `Review` model with migration `003`. Created `shareService.ts`, `SharedReviewPage.tsx` (public read-only view at `/shared/:token`), and wired the new route into `App.tsx`.

**Next steps:**
Finalize tests, run `make check` and `make test-unit`, open draft PR, and request peer review.

**Blockers:** None

---

### Check-in 2 (end of week)

**PR link:** [link to be added after PR is opened]

**Branch:** `feat/101-copy-link-button`

**What you built:**
Added a "Copy link" button to the completed review page that generates a 30-day expiring share token via `POST /reviews/{review_id}/share`, copies the public share URL to the clipboard, and shows inline "Copied!" feedback for 2 seconds. The share URL resolves to a new public `GET /reviews/shared/{token}` endpoint and a read-only `SharedReviewPage` that is accessible without login and expires after 30 days.

**Tests added or updated:**
- `frontend/src/pages/__tests__/ReviewPage.test.tsx` — updated the two reproduction tests (renders "Copy link" button, copies share URL to clipboard) to pass with the new implementation; added a third test asserting the button label changes to "Copied!" after click; mocked `shareService.createShareLink` to return a fixed share URL
- `tests/unit/test_review_service.py` — added `TestShareToken` class with 6 tests: `create_share_token` returns `None` when the review is not found; sets a non-empty token string on the review; sets `share_expires_at` within a 29–31 day window from now; calls `db.commit`; `get_review_by_share_token` returns the review for a valid token; returns `None` for an expired or unknown token

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:**
