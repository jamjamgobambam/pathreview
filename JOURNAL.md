# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
docs/API.md lists every endpoint but only shows the method and path, there's no actual example of how to call them. If I'm setting up this project for the first time, I have no quick way to check that the API is actually working besides poking around in Swagger UI. The fix is to add example curl commands for each endpoint (health, auth, profiles, reviews) so a new contributor can copy, paste, and confirm things work right after running make setup and make run. This only touches docs/API.md, no code changes needed.

**Selection notes:**
I went through the "Is this right for me?" checklist before claiming this. It's scoped to a single doc file, doesn't require touching ingestion/rag/agent internals, and doesn't need me to understand the full RAG pipeline to do it well, just the request/response shape of each endpoint. That made it a good first issue for getting used to the repo and the contribution workflow without taking on a lot of risk.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
