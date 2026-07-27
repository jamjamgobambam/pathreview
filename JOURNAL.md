# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary #101

**Tier:** [ ] Tier 1 [✔] Tier 2 [ ] Tier 3

**Problem summary:**
Right now, the only way to see someone's review summary on PathReview is to be logged into that person's own account, so there's no easy way to hand results to a mentor, recruiter, or peer for feedback. This issue calls for a "Copy link" button on the review page that generates a unique, public URL leading to a read-only version of the summary — no login required. It also needs the link to stop working automatically after 30 days, so a summary isn't left permanently exposed. Getting this working means adding sharing logic to the frontend service and a matching endpoint on the backend to create and validate these time-limited links.

**Why I chose this issue:**
I picked a Tier 2 issue since I'm very comfortable with React from building frontend applications regularly, but have less hands-on experience with the backend/API side of a codebase like this one. I specifically searched the issue tracker for frontend-facing issues, and this one stood out because most of the work (the button, the copy-to-clipboard interaction, and calling the share service) is familiar React territory to me, while the small backend piece (the share-token endpoint) gives me a manageable way to touch the API layer without owning unfamiliar backend logic end-to-end. Also, the 5–8 hour estimate and the scoped files in the issue description felt achievable for this week.

**Branch name:** `feat/101-copy-link-share-summary`

**Setup confirmation:** [✔] App runs locally at localhost:5173

**Cohort ledger:** [✔] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ChinoUkaegbu/pathreview/commit/00997be5dba1b2456fd3334325b1834f0cd68592

**Reproduction summary:**
I found that the "Share" button in `ReviewPage.tsx` already exists and copies a link, but it copies the private, authenticated review URL — which fails for anyone but the logged-in owner since `GET /reviews/{review_id}` requires auth and filters by owner ID, with no public/token-based route or expiration logic anywhere in the codebase.

**PLAN.md link:** https://github.com/ChinoUkaegbu/pathreview/blob/feat/101-copy-link-share-summary/PLAN.md

**Walkthrough video (recommended):** https://drive.google.com/file/d/1-ddXpmBNxSHcOqXTOvw0nA8hOatsjg7c/view?usp=sharing

**Blockers or open questions:**
Still unsure whether share tokens should be actively invalidated when a new one is generated (or if multiple valid tokens per review is fine), and want to confirm the best pattern for mixing an authenticated and a public route within the same FastAPI router.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Backend is fully implemented and committed: added the `ShareLink` model and migration, the `create_share_link` and `get_review_by_share_token` service functions, and the two new API endpoints (`POST /reviews/{review_id}/share` and `GET /reviews/shared/{token}`). Verified end-to-end via Swagger — token generation, public no-auth fetch, and 404s on invalid/unowned requests all work as expected. Also caught and fixed a timezone bug (naive vs. aware datetime comparison) in the `ShareLink.is_expired()` check.

**Next steps:**
Wire up the frontend: add `createShareLink`/`getSharedReview` to `api.ts`, fix `handleShare()` in `ReviewPage.tsx` to use a real share token instead of the raw page URL, and build the new public `/shared/:token` route and page. Then write unit tests for the new service functions.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** [paste link here once opened]

**Branch:** `feat/101-copy-link-share-summary`

**What you built:**
A working public share-link feature: clicking "Share" on a review now generates a real, token-based shareable link that opens a read-only view with no login required, and automatically expires after 30 days.

**Tests added or updated:**
Added 6 tests to `tests/unit/test_review_service.py` covering `create_share_link` (owned review success, not-found/not-owned case) and `get_review_by_share_token` (valid token, unknown token, expired token, and orphaned token whose review no longer exists).

**Self-review confirmation:** [✔] make check passes  [✔] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]