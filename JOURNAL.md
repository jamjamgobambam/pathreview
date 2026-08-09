## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands


**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The current API documentation located in docs/API.md outlines the available endpoints but lacks practical, ready-to-use invocation examples. Because of this missing information, developers setting up the project for the first time face unnecessary friction and cannot easily verify that the API is functioning correctly on their local machines. A successful fix will update the documentation to include clear, copy-pasteable curl commands for the endpoints (such as /auth/login, auth/register, /profiles, /health, or /reviews), enabling developers to immediately test and validate their setups.

**Selection notes / “Is this right for me?” checklist reasoning:** I am selecting this Tier 1 issue because it perfectly aligns with my current comfort level as a new contributor to this specific codebase. While I am comfortable with APIs and data architecture, starting with a Tier 1 documentation task is an ideal way to safely familiarize myself with the project's structure without risking unintended side effects in the core backend logic.
Furthermore, the scope of this issue is an excellent fit for my onboarding process. Instead of simply picking it because it "looked interesting," I chose it because the scope is tightly contained to a single file (docs/API.md). Writing the actual curl commands requires me to actively review and understand the routing, required headers, and request payloads for endpoints like /auth/login and /profiles. This makes it a highly strategic first issue, as it forces me to test the local setup and understand the application's data flow—serving as the perfect stepping stone before taking on more complex Tier 2 or Tier 3 feature tickets.

**Branch name:** docs/117-include-api-example-curl-commands

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/elisathRS/pathreview/commit/a1131b988c93e8278a2e3940d2f09c406eeb782b

**Reproduction summary:**
I reproduced the issue # 117 by reviewing the local API documentation docs/API and comparing it with the available backend routes. The documentation listed the endpoints, but it did not include copy-pasteable curl examples for common flows such as health checks, authentication, profiles, and reviews, which made local validation harder for new contributors.

**PLAN.md link:** https://github.com/elisathRS/pathreview/blob/docs/117-include-api-example-curl-commands/PLAN.md

**Walkthrough video (recommended):**  Not recorded yet

**Blockers or open questions:**
I am determining the scope of this first docs update: should it include the `GET /reviews/{review_id}/status` and `PUT /profiles/{profile_id} routes found in the code, or remain restricted to the existing in `docs/API.md`?

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I updated the main API documentation in docs/API.md. The API reference now includes ready-to-use curl examples for the health check, user registration, login, profile creation, retrieval, and deletion, as well as review creation, retrieval, and listing. I also documented the required Content-Type headers, bearer token authentication, and reusable placeholders for profile and review IDs.

**Next steps:**
I will validate every example against the local API, run make check and make test-unit, request feedback on the existing pull request, and incorporate any clarifications or improvements identified during testing and review.

**Blockers:**
None

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/477

**Branch:** `docs/117-include-api-example-curl-commands`

**What you built:**
I expanded docs/API.md to include comprehensive curl examples for the health, authentication, profile, and review endpoints. The documentation covers JSON, form-encoded, multipart, and bearer-authenticated requests, and illustrates how to reuse profile and review IDs returned by the API.

**Tests added or updated:**
Since this is a documentation-only change, no automated test files were updated. Validation was performed by running the documented commands against the local API, along with the existing make check and make test-unit workflows.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** None


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
Note that no review came in

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Writing curl examples felt like it should be mechanical — read the route, copy the shape into a code block. It wasn't. `/auth/register` takes JSON but `/auth/login` uses `OAuth2PasswordRequestForm`, so it's form-encoded with the email in a `username` field, not JSON — an easy thing to get wrong by assuming the two endpoints are symmetric. I also documented `GET /health`'s response from the schema before actually running it, and got it wrong: the real endpoint returns `503` in this environment because of two bugs in `health.py` (a raw `db.execute("SELECT 1")` that needs `sqlalchemy.text()`, and a reference to `settings.redis_host`/`redis_port` that don't exist on `Settings`). Same thing happened with reviews — I guessed `status: "completed"` and a 0–10 `overall_score`; the real API returns `"complete"` and a 0–1 float. None of that was visible from reading the code alone — I only caught it by actually hitting the running server and comparing.

**What did you learn about working in a large codebase?**
Documentation drifts from behavior fast, and you can't take either the schema or the docstring at face value — you have to run the thing. I also learned that a "tiny, docs-only" issue still touches a surprising amount of the system: auth flow, multipart file uploads, background job status transitions. And commit hygiene isn't cosmetic — it's something the next person inherits. I ended up needing a full history rewrite pass at the end to fix malformed commit messages and to strip out an unrelated `frontend/package-lock.json` diff that had snuck into an early commit, probably from running `npm install` locally during environment setup. That's a much bigger cleanup than if I'd just gotten the commit messages and scope right the first time.

**How did AI tools help — and where did they fall short?**
AI moved fastest on the mechanical work: cross-referencing every route and schema against the docs, running all ten curl examples against the live server in one pass to catch the `status`/`overall_score` mismatches, and handling the `git filter-branch` mechanics of the history cleanup. That sped up the parts of the process that are just labor — typing out commands, comparing JSON shapes, checking file diffs.

Where it fell short was anything requiring judgment instead of execution. It couldn't decide whether to fix the pre-existing `health.py` bugs or just document around them, or whether the stray `frontend/package-lock.json` diff needed to come out of the branch. Those calls stayed mine every time. It also wasn't infallible at the mechanical work itself: a first attempt to fix one commit message with `git filter-branch` silently failed to propagate to later commits, and I only caught it by re-checking the diff instead of assuming the first pass had worked.


**What would you do differently if you started over?**
Run every endpoint against the live local server *before* writing a single example, instead of drafting from the schema first and fixing mistakes after — that would've saved a whole revision pass. I'd also get the commit message format right from the very first commit instead of needing a `git filter-branch` cleanup at the end, and space the two check-ins out properly across the week instead of writing both on the same day.

**What are you most proud of from this module?**
That this is my first real contribution to someone else's repository. Before this module, I'd never had to open a codebase I didn't write, figure out how it's organized, and understand a problem well enough to explain it back clearly — not just to myself, but in a way a reviewer who's never met me could follow. Getting my local development environment running was its own small milestone: docker compose for Postgres and Redis, the right ports, the `.env` values lined up with what the app actually expects. Once that was working, I could stop guessing about how the API behaved and start checking it directly. Learning to navigate the repository — finding the route, then the schema behind it, then the service underneath — is the skill I'll carry into every future issue, more than any individual line I wrote in `docs/API.md`.