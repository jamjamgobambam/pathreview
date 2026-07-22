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

**Reproduction commit link:** https://github.com/ajwadtahmid/pathreview/commit/PENDING

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
