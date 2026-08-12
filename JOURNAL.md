## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists the PathReview HTTP endpoints (health, auth, profiles, and reviews) and points developers to Swagger/ReDoc, but it never shows how to call those endpoints from the terminal. That makes first-time setup harder: after `make run`, there is no copy-paste way to confirm the API is up or to try register/login/profile/review flows without reading OpenAPI interactively. A successful fix adds realistic, copy-pasteable `curl` examples for each documented endpoint (including auth headers and sample JSON bodies where needed) so new contributors can verify the local API quickly against `localhost:8000`.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the documentation plan for issue #117. The API reference now includes
copy-pasteable `curl` commands for authentication, profile management, review
creation and polling, pagination, and cleanup.

**Next steps:**
Validate the commands against the current route contracts, run the project
checks, request draft-PR feedback, and finalize the submission.

**Blockers:**
The repository has pre-existing `make check` and `make test-unit` failures;
the documentation-only change does not modify the affected code.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/354

**Branch:** `docs/117-api-curl-examples`

**What you built:**
Expanded `docs/API.md` into an executable API reference for issue #117. It
documents setup, token and ID capture, request formats, authenticated calls,
asynchronous review polling, pagination, and final cleanup for every public
API route.

**Tests added or updated:**
No application code changed. I verified every documented route and request
format against the current FastAPI route definitions and parsed all Bash code
blocks with `zsh -n`.

**Self-review confirmation:** [x] `make check` introduces no new failures  [x] `make test-unit` introduces no new failures

`make check` has 35 existing lint/type errors and `make test-unit` has 89
existing test errors, all in files outside this documentation-only change.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer or reviewer comments landed on
https://github.com/ascherj/pathreview/pull/354 by the end of Week 10. That
matches the Summer 2026 note that formal reviewer feedback is not a course
feature this term. The PR remains open with the documentation changes for
issue #117.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Getting the local environment fully trustworthy took more work than the docs
issue itself. Docker, seed data, and `make run` got the UI up at
`localhost:5173`, but `/health` still reported Postgres/Redis as unhealthy
because of bugs in the health checker — not because the stack was actually
down. Separately, `make check` and `make test-unit` already fail in unrelated
Python modules, so “green CI” was not a usable signal for a docs-only change.
I also underestimated how picky request formats are: login is OAuth2 form
data (`username`/`password`), not JSON, and profile create is multipart. Those
details only became obvious after reading the FastAPI routes, not from the
original one-line API.md summaries.

**What did you learn about working in a large codebase?**
In your own project you control the whole surface area. Here the useful source
of truth was the route handlers and Pydantic schemas under `api/`, not the
thin markdown that was supposed to explain them. I had to navigate across
auth, profiles, and reviews, notice which endpoints need a bearer token, and
document an async review flow (create → poll) that the old page barely
implied. Contended issues and parallel student PRs also matter: issue #117
had many claimants, so contribution is as much about clear ownership and a
focused, honest PR as it is about the edit itself.

**How did AI tools help — and where did they fall short?**
AI was strongest for orientation — SETUP/CONTRIBUTING, branch naming, drafting
a Week 7 plan, and scaffolding curl examples once the contracts were clear.
It fell short when the repo disagreed with itself: health returning 503 while
the app worked, pre-existing lint/test failures, and the exact login encoding.
Those needed reading `api/routes/*.py`, hitting the live server, and deciding
what belonged in the docs versus what was an unrelated bug. AI also could not
replace the judgment call to mark “no new failures” honestly instead of
pretending the whole suite was clean.

**What would you do differently if you started over?**
I would pick a less crowded issue earlier, or confirm ownership more carefully
before investing Week 8–9 effort, since #117 attracted many overlapping PRs. I
would also verify every curl against a live `make run` session while Docker is
available, instead of relying only on route-source checks when Desktop was
down. Finally, I would add a short “known caveats” note for `/health` sooner,
so readers are not confused by a 503 that does not mean the API is unusable.

**What are you most proud of from this module?**
Turning a sparse endpoint list into a runnable walkthrough — setup variables,
token/ID capture, the right content types per route, review polling, and
cleanup — so a new contributor can exercise the local API from the terminal
without living in Swagger. The journal discipline across Weeks 7–10 also
forced me to leave a clear record of tradeoffs, not just a PR link.
