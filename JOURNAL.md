## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists every endpoint in the PathReview API (health check, auth, profiles, reviews) but only gives a one-line description of each — there's no runnable example showing how to actually call them. That means a new contributor who just finished `make setup` has no fast way to confirm the backend is working end-to-end; they'd have to reverse-engineer request bodies and auth headers from the source code or trial-and-error in Swagger UI. The fix adds a `curl` example under each endpoint (including the auth flow of logging in with one of the seeded test accounts and exporting the resulting JWT for reuse), so a developer can copy-paste their way through health check → login → create profile → request review → fetch review and see the whole system working within a few minutes of finishing setup. I picked this one because it's tightly scoped to a single file (`docs/API.md`), doesn't require touching application code or the database schema, and is a low-risk way to get comfortable with the repo's branch/commit conventions before taking on a Tier 2/3 issue in later weeks.

**Branch name:** docs/117-add-curl-examples

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
