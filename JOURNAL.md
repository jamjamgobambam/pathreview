## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Selection reasoning** I chose this Tier 2 issue because I'm comfortable with React, but haven't worked with shareable URL patterns yet. So the scope felt like a stretch without being too overwhelming.

**Problem summary:**

Right now, completed review summaries in PathReview can only be viewed by the person who generated them, there's no way to share a review with someone else, like a mentor or recruiter. The app is missing a "Copy link" button that would generate a publicly accessible URL for a given review and copy it to the clipboard. A successful fix would add this button to the review detail view in the frontend (ReviewPage.tsx), and likely requires a backend change to support unauthenticated access to a review by a public share token or ID that expires in 30 days.

**Branch name:** feat/101-copy-link-button

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
