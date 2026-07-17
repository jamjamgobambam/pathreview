## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/117

**Issue title:** API docs don't include example curl commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
docs/API.md lists all 10 API endpoints (health, auth, profiles, reviews) but only gives a one-line description for each — there are no example requests, request bodies, headers, or sample responses. A developer setting up the project for the first time has no quick way to confirm the API is actually working without reading backend source to reconstruct the request format. A successful fix adds a runnable curl example (with headers, body, and expected response) for each endpoint in docs/API.md, including the trickier cases like the JWT auth flow and the multipart file upload on POST /profiles.

**Branch name:** docs/117-add-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
Worked through the "Is this right for me?" checklist — this is Tier 1, docs-only (no code/logic changes), touches a single file (docs/API.md), and the estimated effort (2–3 hrs) matches a first issue. Low risk of scope surprises since it doesn't require understanding the ingestion/agent internals, just the existing route signatures.
