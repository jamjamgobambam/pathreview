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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AhmedOHassan/pathreview/commit/f0a6cc0f6ed63c28d0193de23de93184c997fa82

**Reproduction summary:**
I ran the app locally and tried calling a few endpoints using only what docs/API.md tells me. I assumed JSON bodies for auth/login and profile creation since that's the natural guess, but login actually needs an OAuth2 form body and profile creation needs multipart form data with a file upload, neither of which I could tell from the doc. I documented this in a comment at the top of docs/API.md.

**PLAN.md link:** https://github.com/AhmedOHassan/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
Still need to confirm the seeded test accounts from docs/SETUP.md actually work right after a fresh make setup, and I need to figure out the cleanest way to include a sample resume file in the curl example for POST /profiles since there isn't one in the repo already.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md's Plan section are done: I ran the app locally, hit every endpoint in docs/API.md with curl using a real seeded account, and added a verified example and response for each one, plus the shared auth header note. The step 5 re-read (reading the doc as a first-time contributor) caught three real problems that would've broken someone following it top to bottom, a missing resume.md fixture, a profile getting deleted before the reviews section that still needed it, and a misleading empty-list example, all of which I fixed.

**Next steps:**
Run make check and make test-unit as a final baseline check, then open the PR.

**Blockers:**
None. I did find two endpoints that exist in the code but aren't documented at all (PUT /profiles/{profile_id} and GET /reviews/{review_id}/status), I'm leaving those out of scope per PLAN.md and calling them out as a follow-up instead.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** docs/117-api-curl-examples

**What you built:**
I added a runnable curl example and a real example response to every endpoint in docs/API.md, all verified against a local instance. Along the way I actually followed my own doc top to bottom and caught four real problems that would've broken a first-time contributor: a missing resume.md fixture, a profile getting deleted before the reviews section still needed it, a misleading empty-list example, and a curl upload that 422'd because curl doesn't reliably guess a file's MIME type on its own.

**Tests added or updated:**
None, this is a docs-only change to docs/API.md, no code paths were touched.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

make check: 182 pre-existing lint errors, all in files I didn't touch (mostly unused variables in existing test files). make test-unit: 53 pre-existing test failures, 375 passing. Neither command lints or tests docs/API.md, so this docs-only change can't be responsible for either, confirmed by running both before and after my final edits with identical counts.

**Draft PR feedback received from:** none
