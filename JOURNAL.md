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

**PLAN.md link:** [link to PLAN.md on your branch after commit]

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
The health endpoint (`GET /health`) shows postgres and redis as unhealthy
locally due to a pre-existing bug — `api/routes/health.py` reads
`settings.redis_host` and `settings.redis_port` as separate config fields but
`core/config.py` only defines `redis_url` as a combined URL. This is unrelated
to issue #117 but the curl example for /health will need a note clarifying the
discrepancy so it doesn't confuse new developers. No other blockers.
