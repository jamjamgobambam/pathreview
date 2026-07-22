## Solution plan

**Issue:** API docs don't include example curl commands (#117)
https://github.com/jamjamgobambam/pathreview/issues/117

### Understand
This isn't a code bug — it's a documentation gap. `docs/API.md` lists each of
the 10 endpoints with a single-line description and no example request,
headers, body, or response. Expected behavior: a developer can copy a curl
command from the doc and get a working response to confirm the API is
running. Actual behavior: they have to read `api/routes/*.py` to reconstruct
the request format, and two specific mismatches make this worse than a plain
omission:
- `POST /auth/login` uses `OAuth2PasswordRequestForm`, so it requires
  form-encoded `username`/`password` fields. A JSON body (the pattern every
  other POST in the doc implies) returns a `422`.
- `POST /profiles` reads `github_username`/`portfolio_url`/`resume_file` via
  `Form(...)`/`File(...)`, so it's multipart, not JSON. Worse, a JSON body
  doesn't error at all — it returns `200` with the fields silently set to
  `null`, which is a silent-data-loss trap for anyone following the docs.
- Two working endpoints, `PUT /profiles/{profile_id}` and
  `GET /reviews/{review_id}/status`, exist in the router but are missing
  from docs/API.md entirely.

A successful fix adds a runnable, verified curl example (request + response
+ status codes) for all 10 currently-listed endpoints, adds the 2 missing
endpoints to the doc, and calls out the login/profiles encoding gotchas
explicitly so the next developer doesn't hit the same traps.

### Map
Files to touch:
- `docs/API.md` — primary and only file being edited; add curl examples,
  add the 2 missing endpoints, add a short auth walkthrough section.

Files to read only (source of truth for shapes, no changes):
- `api/routes/auth.py`, `api/routes/profiles.py`, `api/routes/reviews.py`
- `api/schemas/user.py`, `api/schemas/profile.py`, `api/schemas/review.py`
- `api/middleware/auth.py`

### Plan
1. Add an "Authentication" walkthrough near the top of API.md: register →
   login (showing the form-encoded curl explicitly, with a callout that this
   endpoint differs from the others) → capture the token → reuse it via
   `Authorization: Bearer <token>` in every subsequent example.
2. Add curl + example response + status codes for `GET /health` and both
   `/auth` endpoints (register success/400-duplicate, login success/401).
3. Add curl + example response + status codes for all 4 `/profiles`
   endpoints — including the multipart file-upload case, the 422 invalid-file
   case, and the previously undocumented `PUT /profiles/{profile_id}` — with
   an explicit note that a JSON body is silently accepted but discarded.
4. Add curl + example response + status codes for all 4 `/reviews`
   endpoints — including pagination query params and the previously
   undocumented `GET /reviews/{review_id}/status`.
5. Re-run every curl example verbatim against a live `make run` stack before
   committing, and paste in the real observed response rather than a
   hand-written guess (already done for all endpoints during Week 8
   reproduction — see JOURNAL.md reproduction notes).

### Inputs & outputs
- Input: the existing docs/API.md structure/section order, and the live
  FastAPI backend as the source of truth for request/response shapes.
- Output: an updated docs/API.md where every endpoint (12 total, including
  the 2 currently missing) has a copy-pasteable curl command, a real example
  response, and its documented status codes — each one verified by actually
  executing it against `localhost:8000`.

### Risks & unknowns
- Resume file parsing (`PyPDF2`) may produce different example text for a
  real PDF vs. the `.md` fixture used during reproduction — want an actual
  small PDF fixture so the documented example is truthful, not fabricated.
- Hardcoding example UUIDs (profile/review IDs) in the doc could look
  confusing after a `make reset-db` produces different IDs — plan to use
  clearly-fake placeholder UUIDs in the doc text but keep the *response
  shape* real.
- `POST /reviews` triggers async background processing
  (`background_tasks.add_task(process_review, ...)`), so the immediate
  response is always `status: "pending"`. Need to decide whether to also
  show a follow-up `GET .../status` poll in the same example to demonstrate
  the async flow, since a reader might otherwise think the review is stuck.
- The `GET /health` endpoint currently reports Postgres/Redis as "unhealthy"
  in my local environment even though the DB is reachable and all DB-backed
  endpoints work — if this is environment-specific, the documented `/health`
  example response should reflect the healthy case, not what I observed
  locally; needs a sanity check before finalizing that example.

### Edge cases
- Invalid or expired JWT on a protected endpoint → 401 example.
- Registering with an email that already exists → 400 example.
- Logging in with a wrong password → 401 example.
- Uploading a resume file that isn't PDF/Markdown/plain text → 422 example.
- Requesting a profile/review ID that doesn't exist or isn't owned by the
  current user → 404 example.
- Out-of-range pagination (`page_size` > 100) on `GET /reviews` → document
  that it silently clamps to 20 rather than erroring, so readers aren't
  surprised.
- Sending a JSON body to `POST /profiles` instead of multipart → document
  explicitly that this "succeeds" with `200` but silently drops the fields,
  since this is the single most likely mistake a doc reader would make.
