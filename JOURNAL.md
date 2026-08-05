## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API reference in `docs/API.md` documents each endpoint’s purpose and
parameters, but it never shows how to call them. Without sample `curl`
invocations, someone bringing the project up for the first time has no quick
way to confirm the server is responding as expected. Filling in those
examples would make the docs a practical smoke-test guide as well as a
reference.

**Is this right for me?**
- [x] Scope is clear — one file (`docs/API.md`); add example `curl` calls for documented endpoints
- [x] Effort fits — labeled Tier 1 / good first issue; estimated 2–3 hours
- [x] Skills match — documentation + basic HTTP/`curl`; no deep backend or RAG changes required
- [x] Verifiable — I can run the API locally and confirm each example returns a sensible response
- [x] Unblocked — app setup is confirmed; work does not depend on unfinished features elsewhere

**Selection notes:** This is a focused docs gap rather than a bug hunt. The API surface in
`docs/API.md` is small (health, auth, profiles, reviews), so adding copy-pasteable
examples is a concrete, reviewable change that still teaches me the real request shapes
and auth flow. That makes it a good first contribution without overcommitting scope.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduce & plan

**Reproduction steps:**
1. Opened `docs/API.md` and confirmed every endpoint is described with no example `curl` invocations.
2. With the API running locally, ran:
   ```bash
   curl -s http://localhost:8000/health
   ```
3. Received a JSON health payload (HTTP 503 / `"status":"unhealthy"`) with
   `postgres` and `redis` marked unhealthy and `vector_db` healthy. That
   proves the API is reachable; the unhealthy flags look like known probe bugs
   (#154 SQLAlchemy `text()` usage, #155 missing `redis_host` on Settings), not
   a missing-docs problem.
4. Gap location: `docs/API.md` only — listings for Health, Auth, Profiles, and
   Reviews with no copy-pasteable examples.

**What a successful fix will add:** Working `curl` examples under each endpoint
section so a first-time setup can smoke-test the API from the docs alone.

**Solution plan:** See [`PLAN.md`](./PLAN.md) — approach, files to touch,
example `curl` sketches, risks (#154/#155 health quirks, login form vs JSON),
and a docs-only test plan for issue #117.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Renamed the working branch to `docs/117-api-curl-examples` to match
`CONTRIBUTING.md`. Implemented the core PLAN.md work: added copy-pasteable
`curl` examples under Health, Authentication, Profiles, and Reviews in
`docs/API.md`, including seed-user login (form-encoded), Bearer token reuse,
and multipart profile create. Documented the known `/health` 503 quirk so
readers are not blocked.

**Next steps:**
Open a draft PR against upstream, request peer/mentor feedback in Slack, run
`make check` and `make test-unit` and note any pre-existing failures, then
finalize the PR template and Check-in 2 with the PR link.

**Blockers:**
None so far — this is a docs-only change, so no new unit tests are required
beyond confirming existing suites are not worsened.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/572

**Branch:** `docs/117-api-curl-examples`

**What you built:**
Updated `docs/API.md` with copy-pasteable `curl` examples for every documented
endpoint (health, auth, profiles, reviews). Examples match real request shapes —
JSON register, OAuth2 form login, multipart profile create, and Bearer-auth
reviews — so a first-time setup can smoke-test the API from the docs alone.

**Tests added or updated:**
Docs-only change — no unit test files updated. Verified with local `curl`
against `/health` and by matching examples to `api/routes/*.py` request shapes.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Note: “passes” here means this PR introduces no new failures. Pre-existing
issues remain: `make lint` reports many unrelated Ruff findings; `make test-unit`
had 53 failed / 375 passed before and after this docs-only change.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments arrived on PR #572 by the end of the week.
(Su26: formal reviewer feedback is not provided this cohort.)

**How you responded:**
N/A — no feedback to address.

---

### Reflection

**What was harder than you expected?**
Local environment setup took more energy than the docs change itself. First
`make setup` failed because Docker wasn’t installed and Alembic hit a local
Postgres without a `pathreview` role; later `/health` returned 503 with
postgres/redis “unhealthy,” which looked like another infra failure until I
read `api/routes/health.py` and realized the probes themselves are buggy
(#154/#155). Separately, I almost documented login as JSON — the handler uses
OAuth2 form fields (`username`/`password`), which only became obvious by
reading `api/routes/auth.py`.

**What did you learn about working in a large codebase?**
You can’t invent the “right” example from the markdown alone. Matching
`docs/API.md` to real routes and schemas (multipart profiles, form login,
Bearer headers) mattered more than polishing prose. I also learned that
`make check` / `make test-unit` can fail for reasons unrelated to your PR:
the bar for a docs contribution was “don’t make it worse,” which meant
documenting pre-existing failures instead of trying to green the whole suite.
Conventions in `CONTRIBUTING.md` (branch names with issue numbers, conventional
commits) are part of the contribution, not optional polish.

**How did AI tools help — and where did they fall short?**
AI was strongest for scaffolding: `PLAN.md`, journal templates, PR description
wording, and pointing me at the right route files. It fell short when the
machine state was wrong — “role pathreview does not exist” and Docker-not-
installed errors needed real environment fixes, not more generated markdown.
Trusting the `/health` JSON without reading the health route would have sent
me down the wrong rabbit hole; AI suggested useful next checks only after I
pasted the actual response.

**What would you do differently if you started over?**
I’d install Docker and finish `docker compose up -d` / `make setup` before the
first migration attempt, copy `.env.example` immediately, and name the branch
`docs/117-...` from day one instead of renaming later. I’d also open the draft
PR earlier in Week 9 so Slack peer feedback had time to land before Check-in 2.

**What are you most proud of from this module?**
Getting the curl examples to match real request shapes — especially form-encoded
login and multipart profile create — so a first-time setup can smoke-test the
API from the docs without guessing. The four-week cadence (select → reproduce →
plan → ship PR → reflect) felt more like real open-source practice than a
one-shot homework dump.
