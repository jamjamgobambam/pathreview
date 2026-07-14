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
