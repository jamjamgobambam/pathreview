## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists every endpoint with a one-line description of what it does,
but none of them show an actual example request or response. A developer
setting up PathReview for the first time has no copy-pasteable way to hit an
endpoint and confirm the API is actually responding — they'd have to read the
route source or guess at the request body shape themselves. While comparing
the doc against the real routes in `api/routes/`, I also noticed the docs are
missing two endpoints entirely: `PUT /profiles/{profile_id}` and
`GET /reviews/{review_id}/status` are both implemented in the code but aren't
listed in `docs/API.md` at all. A successful fix adds a working `curl` example
for every documented endpoint and brings the two missing routes into the doc,
so a new contributor can verify a fresh install end-to-end from the README
alone.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## "Is this right for me?" checklist reasoning

**Part 1 — Understanding the issue**
- I can paraphrase it without re-reading: `docs/API.md` describes each endpoint
  but never shows a real request, so nobody can quickly confirm the API works
  after setup. ✓
- Relevant files located and confirmed to exist: `docs/API.md`, and I grepped
  every actual route in `api/routes/` (`auth.py`, `profiles.py`, `reviews.py`,
  `health.py`) to see what should be documented. ✓
- Before/after is concrete: before, a new contributor reads a one-line
  description and has to guess the request shape; after, every endpoint has a
  copy-pasteable `curl` command showing a real request and response, and the
  two currently-undocumented routes (`PUT /profiles/{profile_id}`,
  `GET /reviews/{review_id}/status`) are listed. ✓

**Part 2 — Tier fit**
- Tagged Tier 1 on the tracker, and this is my first time contributing to a
  codebase this size, so a Tier 1 pick is the right call rather than reaching
  for Tier 2/3 to prove something. ✓

**Part 3 — Codebase readiness**
- I opened `docs/API.md` directly and read every listed endpoint, then grepped
  `@router\.` across `api/` to see the actual route definitions and compare
  against the doc — not just a filename match. ✓
- I understand the file well enough to plan the fix: for each endpoint, note
  its method/path/request body from the route source, then add a `curl -X
  <method> ... -d '{...}'` block plus a sample JSON response under it in
  `docs/API.md`. ✓
- Test file: this issue is docs-only (`docs/API.md`), so there's no
  corresponding unit test to update — nothing in `tests/unit/` covers markdown
  documentation. I confirmed this by checking `tests/unit/` for any doc-related
  test and finding none, rather than assuming. The verification step for this
  issue will instead be running each `curl` example against the live app to
  confirm the example itself is accurate, which I'll do in Weeks 8–9.

**Part 4 — Scope and time**
- Checked the issue comments and the cohort ledger's Claims count before
  committing — comfortable with how many others are on it.
- The issue's own estimate is 2–3 hours, which matches a Tier 1 docs task:
  read each route, write and verify one curl example per endpoint (9 routes
  total, plus documenting the 2 missing ones). Realistic for Weeks 8–9 given
  my other commitments.
- No blockers or dependencies mentioned on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shanekellyreyes/pathreview/commit/d0729a4
**PLAN.md link:** https://github.com/shanekellyreyes/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Reproduction summary:**
Confirmed the issue by running all 11 API endpoints locally using manually
constructed curl commands (since the doc provides none). The most concrete
reproduction: attempting `POST /auth/login` with a JSON body returns 422
because the endpoint uses OAuth2 form data — a gotcha invisible from the doc.
Two endpoints (`PUT /profiles/{profile_id}` and `GET /reviews/{review_id}/status`)
are implemented in the route files but missing from `docs/API.md` entirely.

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
The health endpoint (`GET /health`) shows postgres and redis as unhealthy
locally due to a pre-existing bug — `api/routes/health.py` reads
`settings.redis_host` and `settings.redis_port` as separate config fields but
`core/config.py` only defines `redis_url` as a combined URL. This is unrelated
to issue #117 but the curl example for /health will need a note clarifying the
discrepancy so it doesn't confuse new developers. No other blockers.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implementation complete. Updated `docs/API.md` with working curl examples for
all 11 endpoints — 9 that were described but had no examples, plus 2 that were
implemented in the route files but missing from the doc entirely
(`PUT /profiles/{profile_id}` and `GET /reviews/{review_id}/status`). Added an
auth explanation section and a callout on the login endpoint's OAuth2 form data
requirement, which silently 422s if a developer sends JSON instead. Added
`tests/unit/test_api_docs.py` with 6 regression tests. All 6 pass. The existing
suite has 53 pre-existing failures across unrelated modules — none introduced by
this change.

**Next steps:**
Open the PR, fill out the template, mark ready for review, submit.

**Blockers:**
None. `make check` reports 182 pre-existing lint errors in unrelated files —
none in files touched by this PR.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/823

**Branch:** `docs/117-api-curl-examples`

**What you built:**
Added working curl examples to `docs/API.md` for all 11 API endpoints, including
an auth section, a warning about the login endpoint's OAuth2 form data
requirement, and documentation for two routes (`PUT /profiles/{profile_id}` and
`GET /reviews/{review_id}/status`) that were implemented but not listed in the
original doc.

**Tests added or updated:**
Added `tests/unit/test_api_docs.py` — 6 tests verifying the doc file exists,
all endpoint sections are present including the two newly documented routes,
curl examples are included, and the form-data warning is documented.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in before the end of the course. This is noted
as normal per the module guide — maintainers are often volunteers with
limited time, and a PR without a review is not a failed contribution.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
The environment setup was harder than expected — not conceptually, but in
practice. Docker containers have to be running and healthy before `make run`,
and if you start the app first the connection pool initializes with dead
connections and silently stays broken until you restart. There's no obvious
error message pointing to the real cause. I lost real time to this across
multiple sessions before I understood the startup sequence well enough to
do it reliably. I'd flag that as the single most friction-causing part of
the whole module.

The other thing that surprised me was the test question for a docs-only
change. The testing guide assumes you're touching a Python function — it
says to find the test file for the module you changed and match the pattern.
But `docs/API.md` is a markdown file. There is no test file for it. I had
to reason through a reasonable approach from scratch: regression tests that
check the markdown file contains the expected endpoints and curl examples.
It works and it's legitimate, but it wasn't something I could just look up.

**What did you learn about working in a large codebase?**
The biggest thing was how much the pre-existing state of the codebase
shapes your work. `make check` reported 182 lint errors and `make test-unit`
had 53 failing tests before I touched a single file. In my own projects,
a failing test means I broke something. Here it meant I needed to understand
the baseline before I could say anything meaningful about whether my changes
made things better or worse. That shift — from "all tests should pass" to
"my changes should not introduce new failures" — is a real adjustment.

I also learned how important it is to read the actual code rather than
trust a description of it. The login endpoint's form-data requirement is
not mentioned anywhere in the existing docs. I only found it by reading
`api/routes/auth.py` and seeing `OAuth2PasswordRequestForm`. If I had
written the curl example from memory or from a summary, it would have
shown JSON and been wrong.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation — summarizing what route files do,
explaining the FastAPI dependency injection pattern, helping me understand
what `OAuth2PasswordRequestForm` means in practice. That kind of "explain
this code to me" use saved real time.

Where it fell short: AI predicted that issue #3 in a previous project
(duplicate search results) was a many-to-many join fan-out bug fixable
with `.distinct()`. When I reproduced it, the bug didn't manifest — SQLAlchemy
2.0 de-duplicates ORM entity queries automatically. I would have submitted
a fix for a bug that didn't exist if I hadn't run the reproduction first.
That's the lesson: AI can generate a plausible explanation, but plausible
is not the same as correct. You have to verify against the real system.

**What would you do differently if you started over?**
Start Docker Desktop before doing anything else, every session, without
thinking about it. That's the obvious one.

Less obviously: I'd open the draft PR in Week 8 rather than Week 9. The
assignment says not to wait until the due date, and I understand why now —
getting feedback before the final submission would have been more valuable
than getting it after. Even if no maintainer reviewed it, the act of
writing the PR description early would have clarified my thinking about
what I was actually building and why.

**What are you most proud of from this module?**
The reproduction work from Week 8. I actually ran all 11 endpoints against
the live API and captured real response shapes before writing a single
example. That's what made the curl examples accurate rather than
plausible-looking-but-wrong. The login form-data gotcha — `POST /auth/login`
returns 422 if you send JSON instead of form data — is something I only
caught by hitting the endpoint myself and seeing it fail. That observation
is probably the most useful thing in the entire PR, and I only found it
because I did the reproduction properly rather than skipping it.