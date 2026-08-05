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

**PR link:** https://github.com/ascherj/pathreview/pull/500

**Branch:** docs/117-api-curl-examples

**What you built:**
I added a runnable curl example and a real example response to every endpoint in docs/API.md, all verified against a local instance. Along the way I actually followed my own doc top to bottom and caught four real problems that would've broken a first-time contributor: a missing resume.md fixture, a profile getting deleted before the reviews section still needed it, a misleading empty-list example, and a curl upload that 422'd because curl doesn't reliably guess a file's MIME type on its own.

**Tests added or updated:**
None, this is a docs-only change to docs/API.md, no code paths were touched.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

make check: 182 pre-existing lint errors, all in files I didn't touch (mostly unused variables in existing test files). make test-unit: 53 pre-existing test failures, 375 passing. Neither command lints or tests docs/API.md, so this docs-only change can't be responsible for either, confirmed by running both before and after my final edits with identical counts.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
No feedback came in on the PR. Per the Su26 note, reviewer feedback isn't a feature this term, so there was nothing to receive.

**How you responded:**
N/A, no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Actually verifying the doc instead of guessing was the hard part, not writing it. I assumed I'd just read the route files, figure out the request shapes, and write curl examples from that. Instead I had to stand up the whole local environment (docker compose for postgres/redis/vector-db, run migrations, seed the db, run the backend) just to confirm each example actually worked, and even then I still shipped a broken curl command on my first pass (the resume upload 422'd because curl doesn't reliably guess a file's MIME type from its extension). I only caught that because I went back and literally followed my own doc step by step like a first-time contributor would, and it broke immediately. If I hadn't done that re-read, a "verified" doc would have shipped with a command that doesn't work.

**What did you learn about working in a large codebase?**
Even a docs-only issue touches a lot of surface area once you take "verified" seriously. To write one accurate paragraph about POST /reviews, I had to trace through the route, the schema, and the fact that review generation runs in the background, which meant the response I documented had to reflect a pending state, not a finished one. I also ran into two endpoints (PUT /profiles/{profile_id} and GET /reviews/{review_id}/status) that exist in the code but aren't documented anywhere, and had to consciously decide not to fix that since it was outside issue #117's scope. In my own projects I'd have just fixed it since I own the whole thing. In someone else's codebase, scope discipline is part of the job, not an afterthought.

**How did AI tools help, and where did they fall short?**
AI was genuinely useful for exploring the codebase fast, finding the exact route and schema files I needed to reference in PLAN.md, and for restructuring/rewording the doc once I knew what needed to change. Where it fell short was verification. AI happily wrote a plausible-looking empty-review-list example and a resume-upload curl command that looked correct but wasn't, because it hadn't actually run either of them. Every real bug I found and fixed (the missing resume.md fixture, the profile getting deleted before reviews needed it, the MIME type issue) only surfaced because I ran the commands myself against a live local instance, not because the AI caught them on its own. The lesson was to treat AI-written docs and code the same way, as a draft that needs to be run before it can be trusted.

**What would you do differently if you started over?**
I'd do the "follow my own doc as a first-time contributor" pass earlier, before considering any section done, instead of treating it as a final step at the end. I did this eventually per PLAN.md's own step 5, but I wrote most of the doc first and only stress-tested it afterward. Doing that check endpoint by endpoint as I went would have caught the MIME type issue and the delete-ordering issue immediately instead of in a separate pass.

**What are you most proud of from this module?**
Catching my own mistake with the resume upload MIME type. It would have been easy to consider the PR done since every response in the doc really was captured from a real curl run at some point. Going back and actually re-running the doc's instructions from scratch, and treating a 422 I got as a real bug in my own work rather than a fluke, felt like the most honest version of "verify, don't guess" that I could have applied to this issue.
