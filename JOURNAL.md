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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/830462d29af84a0ad3bed316b4756ecb026078bb

**Reproduction summary:**
I confirmed the gap by running the app locally and clicking the existing Share button on a completed review. The button copies the current page URL to the clipboard, but that URL requires authentication — opening it in an incognito window redirects to the login page instead of showing the review. I also audited the codebase and found that `frontend/src/services/shareService.ts` does not exist, `api/routes/reviews.py` has no endpoint for generating or validating share tokens, and there is no database model for storing tokens. The public shareable link feature is entirely unimplemented.

**PLAN.md link:** https://github.com/rose413/pathreview/blob/feat/101-copy-link-button/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
I am uncertain whether other files beyond the three listed in the issue will need to change. Specifically, I expect to also need a new database model for share tokens, an Alembic migration, and a new Pydantic schema — none of which are mentioned in the original issue description.