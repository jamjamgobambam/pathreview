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


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ajwadtahmid/pathreview/commit/9f82436

**Reproduction summary:**
Ran every endpoint in docs/API.md against the local stack (`make run`, seeded
test account) using only the information the current doc provides, then
compared against the actual route code. Two silent traps confirmed: `/auth/login`
rejects JSON with a 422 and requires form-encoded `username`/`password`, and
`POST /profiles` doesn't error on a JSON body at all — it returns `200` but
silently discards the submitted fields since they're only read via `Form(...)`.
Also confirmed two endpoints (`PUT /profiles/{id}`, `GET /reviews/{id}/status`)
exist in `api/routes/` but are entirely absent from docs/API.md.

**PLAN.md link:** https://github.com/ajwadtahmid/pathreview/blob/docs/117-add-api-curl-examples/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
- `GET /health` reports Postgres/Redis as "unhealthy" even though a direct
  `psql` connection succeeds and every DB-backed endpoint (register, profile,
  review) works correctly — looks like a bug in the health check's own
  connectivity test, unrelated to #117's scope. Flagging in case it's worth a
  separate issue later.
- Need a real small PDF fixture (not just a `.md` file) to capture a truthful
  PyPDF2-parsed resume-upload response for the final docs example, rather
  than a fabricated one.

### Reproduction notes (verified against running API, 2026-07-21)

All commands run against `http://localhost:8000` after `make setup && make run`,
using the seeded account `user1@example.com` / `password1` (a fresh test user
was used in practice; behavior is identical).

**1. `/auth/login` — docs give no hint this needs form encoding, not JSON**
```bash
# Naive attempt per the current one-line doc entry:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","password":"password1"}'
# -> 422 {"detail":[{"type":"missing","loc":["body","username"],...}]}

# Actual working form (OAuth2PasswordRequestForm):
curl -X POST http://localhost:8000/auth/login \
  -d "username=user1@example.com&password=password1"
# -> 200 {"access_token":"...","token_type":"bearer"}
```

**2. `POST /profiles` — worse than an error: silently drops data**
```bash
# Naive JSON attempt does NOT fail — it succeeds with empty fields:
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"github_username":"octocat","portfolio_url":"https://example.com"}'
# -> 200 {"id":"...","github_username":null,"portfolio_url":null,...}

# Correct multipart form:
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://example.com"
# -> 200 {"id":"...","github_username":"octocat","portfolio_url":"https://example.com",...}
```

**3. Undocumented endpoints confirmed working**
```bash
curl -X PUT http://localhost:8000/profiles/{profile_id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"github_username":"octocat-updated","portfolio_url":"https://updated.example.com"}'
# -> 200, updates profile fields — not listed anywhere in docs/API.md

curl http://localhost:8000/reviews/{review_id}/status \
  -H "Authorization: Bearer <token>"
# -> 200 {"review_id":"...","status":"complete","progress_pct":0} — also undocumented
```

**4. Everything else matched the docs' implied behavior**
- `GET /health` → 200/503 with a dependency breakdown
- `POST /auth/register` → 200 with token; 400 on duplicate email
- File upload validation → 422 for non-PDF/Markdown/plaintext; 200 with
  `resume_filename` set for a valid `.md` upload
- Auth guard → 401 with no token; 404 for another user's profile/review ID
- `GET /reviews` pagination → out-of-range `page_size` (e.g. 500) silently
  clamps to 20, no error
- `DELETE /profiles/{id}` → 204, and a follow-up GET correctly 404s


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all 4 sub-tasks from PLAN.md: the authentication walkthrough
section, curl examples for `/health` and `/auth`, curl examples for all 4
`/profiles` endpoints (including the previously-undocumented `PUT`), and
curl examples for all 4 `/reviews` endpoints (including the
previously-undocumented `GET .../status`). Every example was executed
against a live `make run` stack and the real observed response was pasted
in, not hand-written.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md`, confirm `make check` and
`make test-unit` show no new failures beyond the documented pre-existing
ones, then open a draft PR for peer/mentor feedback.

**Blockers:**
None blocking. While verifying examples I found two real bugs unrelated to
#117's scope: `GET /health` reports `postgres` as unhealthy even when the DB
is reachable (raw SQL string instead of `text()`), and PDF resume uploads
always fail with 422 (route imports `PyPDF2`, project depends on `pypdf`).
Documented both with notes in docs/API.md instead of fabricating a working
example, and flagged them for a separate issue.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/290

**Branch:** `docs/117-add-api-curl-examples`

**What you built:**
Expanded `docs/API.md` from one-line endpoint descriptions into a full
reference: a live-verified curl example, real response, and status codes
for all 12 endpoints (10 originally listed plus 2 that existed in the
router but were undocumented), plus an authentication walkthrough and
explicit callouts for two request-format traps (`/auth/login`'s
form-encoding requirement and `/profiles`'s silent JSON-body data loss).

**Tests added or updated:**
None. This is a documentation-only change with no application code
touched; the live-executed curl examples themselves are the verification.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both with the pre-existing-failures caveat documented in the PR description
— no new failures introduced by this change)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback received as of submission.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
I picked #117 specifically because it was Tier 1 and docs-only, expecting a
fairly mechanical task: read the routes, write curl commands, done. What I
didn't expect was how much verification work a "just write down what already
exists" issue actually requires. Two of the ten originally-documented
endpoints had behavior that contradicted the obvious reading of the route
code (`/auth/login` looking like every other JSON POST until you actually
hit the `OAuth2PasswordRequestForm` dependency; `/profiles` accepting a JSON
body without erroring at all, just silently nulling every field). Neither
of those would have been obvious from a read-through — I only found them by
actually executing every example against a live stack instead of trusting
my own reading of `api/routes/*.py`. That reflex, run it before you write
it down, ended up being the actual work of the issue, not the curl syntax.

**What did you learn about working in a large codebase?**
The gap between what code appears to do and what it actually does when run
is bigger than I expected, and it's not always a logic bug — sometimes it's
an environment mismatch you'd never catch by reading. The PDF resume upload
path looks completely correct in `api/routes/profiles.py` (`import PyPDF2`,
parse the pages, return the text), but the project's dependency is `pypdf`,
not `PyPDF2`, so every PDF upload has been silently 422ing since whenever
that dependency was added. Nothing in the code itself signals that; you only
find it by running the code in the actual environment it ships in. In my
own projects I control both the code and the environment at all times, so
that class of bug barely exists. In someone else's production codebase, the
two can drift apart without anyone noticing, and a contributor writing docs
is one of the few people who has a reason to actually exercise every path.

**How did AI tools help — and where did they fall short?**
AI assistance (Claude Code) was most useful for the parts that are
mechanical once you know the answer: reading `api/routes/*.py` and
`api/schemas/*.py` quickly to identify field shapes, drafting consistent
curl/JSON formatting across a dozen endpoints without me having to hand-type
each one, and catching a self-review inconsistency I'd introduced myself
(a real captured UUID left in one request body while every other example
used a `{profile_id}` placeholder). It fell short at the one thing that
actually mattered for this issue: knowing whether an example was *true*.
Left unchecked, it would have been easy to generate a plausible-looking PDF
upload response instead of running one, and that response would have been
wrong. The only way to catch that was to distrust generated output by
default and re-run every single example against the live API before
committing it, which is slower than just writing docs from the route code,
but it's the actual point of the issue.

**What would you do differently if you started over?**
I'd request peer or mentor feedback on the draft PR before finalizing it,
rather than skipping straight from "self-review passes" to "mark as ready
for review." I made that call because I didn't think feedback would arrive
in time, but it means I have no outside check on two judgment calls I made
solo: how much detail to put in the two bug callouts (health check,
PDF upload) versus how much is scope creep for a docs issue, and whether
the authentication walkthrough section is genuinely clearer for a first-time
reader or just clearer to me because I already know the flow. Both are
exactly the kind of thing a second pair of eyes catches that self-review
doesn't.

**What are you most proud of from this module?**
Catching the `POST /profiles` JSON-body silent data loss case specifically.
It's not the flashiest thing in the PR, but it's the one most likely to
actually cost someone real time: it doesn't error, it doesn't warn, it
returns a normal-looking 200 with a profile object that just happens to have
every field set to `null`. A developer following the old docs would create
a "successful" profile with no data in it and have no idea why until they
went and read the route source, which is exactly the problem #117 was filed
to fix. Finding it wasn't clever, it just meant not stopping at the first
successful-looking response and treating the "succeeds but looks off" cases
as seriously as the ones that outright error.
