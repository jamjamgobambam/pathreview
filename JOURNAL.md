## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/101]

**Issue title:** [Add a "Copy link" button to share a public review summary]

**Tier:** [ ] Tier 1  [ X ] Tier 2  [ ] Tier 3
Tier 2 fits my current scope because the feature spans both the frontend and backend — it requires building a new UI button in React, a service layer for generating share tokens, and a new API route in Python. I have prior experience with full-stack development, so I'm comfortable working across those layers, but the token expiry logic and public-access design add enough complexity to make this a meaningful challenge rather than a trivial addition.

**Problem summary:**
Users currently have no way to share their review summary with others — there is no shareable link feature in the application. The missing functionality should allow a user to generate a public, read-only link to their review summary that anyone can view without needing to log in. A successful fix would add a "Copy link" button to the review page that creates a time-limited share token (expiring after 30 days) and returns a public URL. This primarily affects `frontend/src/pages/ReviewPage.tsx`, `frontend/src/services/shareService.ts`, and `api/routes/reviews.py`.

**Branch name:** [feat/101-copy-link-button]

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger
