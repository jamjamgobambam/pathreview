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
