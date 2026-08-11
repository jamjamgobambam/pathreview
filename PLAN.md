## Solution plan

**Issue:** [API docs don't include example `curl` commands #117](https://github.com/ascherj/pathreview/issues/117)

### Understand
`docs/API.md` documents each endpoint with a one-line description but no example
invocations. A developer setting up PathReview for the first time cannot quickly
verify the API is working — they'd have to read the route source code or guess
at request body shapes and authentication requirements.

Expected behavior: every endpoint in `docs/API.md` has a working `curl` example
showing the exact request and a representative response.

Actual behavior: `docs/API.md` has only a one-line description per endpoint, no
request examples, no response examples, and no indication of which endpoints
require authentication. Two implemented endpoints (`PUT /profiles/{profile_id}`
and `GET /reviews/{review_id}/status`) are also missing from the doc entirely.

I reproduced the issue by running the API locally and manually constructing
requests from the route source code — exactly the friction the doc should
eliminate.

### Map
**Files to touch:**
- `docs/API.md` — the only file that needs to change. This is a documentation-
  only fix; no application code is modified.

**Files read for reference (no changes):**
- `api/routes/health.py` — GET /health response shape
- `api/routes/auth.py` — register/login request shapes and auth behavior
- `api/routes/profiles.py` — profile endpoints, multipart form vs JSON, auth
- `api/routes/reviews.py` — review endpoints, pagination params, status shape

### Plan
1. **Add authentication note** at the top of the Endpoints section explaining
   which endpoints require a Bearer token and how to obtain one (register or
   login first).

2. **Add curl examples for all existing documented endpoints** (GET /health,
   POST /auth/register, POST /auth/login, POST /profiles, GET /profiles/{id},
   DELETE /profiles/{id}, POST /reviews, GET /reviews/{id}, GET /reviews).
   Each example shows the exact curl command and a truncated but representative
   response body, verified against the live API.

3. **Add the two missing endpoints** to the doc with curl examples:
   - `PUT /profiles/{profile_id}` — update github_username and/or portfolio_url
   - `GET /reviews/{review_id}/status` — returns {review_id, status, progress_pct}

4. **Add a note on the login endpoint's form-data requirement** — this is the
   single biggest gotcha: /auth/login uses OAuth2PasswordRequestForm (form
   fields with -F, not JSON with -d). Without an example, a developer will
   almost certainly send JSON and get a 422 error.

5. **Verify every example** by running each curl against the live local API and
   confirming it returns the expected status code and response shape.

### Inputs & outputs
**Input:** the current `docs/API.md` with one-line endpoint descriptions and
no examples.

**Output:** an updated `docs/API.md` where every endpoint (11 total, including
the 2 currently undocumented ones) has:
- The HTTP method and path
- Auth requirement (Bearer token or open)
- A complete curl command that works against `http://localhost:8000`
- A representative JSON response

No application code changes. No new files. One file modified.

### Risks & unknowns
- **Token expiry in examples:** JWT tokens expire. The examples need to use a
  placeholder like `$TOKEN` rather than a real token value, with a note
  explaining how to obtain a fresh one via register or login.

- **POST /profiles is multipart, not JSON:** this is the most common mistake —
  the endpoint uses `-F` form fields, not `-d` JSON. The example must show this
  correctly or it will mislead rather than help.

- **DELETE /profiles/{id} returns 204 No Content:** curl with `-v` or `-I`
  should be used to show the status code, since there's no response body to
  display.

- **The health check shows postgres/redis as unhealthy locally** due to a bug
  in `api/routes/health.py` — it reads `settings.redis_host` and
  `settings.redis_port` as separate fields, but `core/config.py` only defines
  `redis_url` as a combined URL. This is a pre-existing bug unrelated to this
  issue; the curl example should note that the health endpoint may show
  unhealthy for redis/postgres even when the app is functioning normally.

### Edge cases
- A user who runs the curl examples before registering will get a 401 — the
  examples need to be sequenced (register → login → get token → use token).
- A user who sends JSON to `/auth/login` instead of form data gets a 422
  Unprocessable Entity — the example must use `-F`, not `-H "Content-Type:
  application/json" -d`.
- Profile IDs and review IDs in the examples must be clearly marked as
  placeholders (e.g. `<profile-id>`) so readers know to substitute their own
  values.
- `GET /reviews` without a profile filter returns all reviews for the
  authenticated user — the example should show the `?page=1&page_size=20`
  query params so readers know pagination is available.
