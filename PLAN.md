# Solution plan

**Issue:** [API docs don't include example curl commands #117](https://github.com/ascherj/pathreview/issues/117)

### Understand

Not a bug in code — a documentation gap. `docs/API.md` lists every endpoint by
method and path (e.g. `POST /auth/register — Create a new account.`) but
gives no runnable example, no request body shape, no auth header, no response
shape.

- **Expected:** a developer who finishes `make setup` can open `API.md`, copy
  a `curl` command, and confirm the API is alive without reading source or
  clicking through Swagger.
- **Actual:** they have to open http://localhost:8000/docs (Swagger),
  reverse-engineer bodies from the pydantic schemas, or guess. That's a
  friction point on the first-run experience.

Root cause of the *documentation* gap: the file was written as a table of
contents, not a reference. Someone captured the surface (routes exist) and
never came back to fill in the depth (how to call them).

### Map

Touching one file:
- `docs/API.md` — the only file that changes.

Read-only, to get request/response shapes right:
- `api/schemas/user.py` — `UserCreate`, `UserLogin`, `Token`
- `api/schemas/profile.py` — `ProfileCreate/Update/Response`
- `api/schemas/review.py` — `ReviewCreate/Response`, `ReviewListResponse`,
  `FeedbackSection`
- `api/routes/auth.py` — confirms `/auth/login` uses
  `OAuth2PasswordRequestForm` (form-encoded, not JSON — easy to get wrong)
- `api/routes/profiles.py` — confirms `POST /profiles` is multipart/form-data
  with an optional file upload, and reveals an undocumented
  `PUT /profiles/{id}`
- `api/routes/reviews.py` — reveals an undocumented
  `GET /reviews/{id}/status` and the pagination query params on `GET /reviews`
- `api/routes/health.py` — confirms the nested response shape and 503 behavior

### Plan

1. **Read the schemas first.** They're the authoritative source of field
   names and types. Never guess a body — copy from the pydantic model.
2. **Cross-check each schema against its route file.** The schema tells you
   the JSON body; the route tells you whether it's actually JSON, form, or
   multipart, and whether auth is required. This is where the login and
   profile inaccuracies surface.
3. **Note anything the docs miss entirely** (`PUT /profiles/{id}`,
   `GET /reviews/{id}/status`, pagination params on `GET /reviews`) and add
   them under the endpoint group they belong to. Scope creep is minimal — one
   file, still docs.
4. **Rewrite `API.md` inline** — put the curl example directly under each
   endpoint description rather than in a separate "Examples" section. Keeps
   the file scannable and avoids duplicating endpoint headings.
5. **Add a token-export snippet once** near the top so subsequent examples
   can reference `$TOKEN` and `$PROFILE_ID` instead of pasting a JWT into
   every command.

### Inputs & outputs

- **Input:** the current `docs/API.md`, the schema files, the route files.
- **Output:** an updated `docs/API.md` where every endpoint has (a) a runnable
  `curl` command with correct method/headers/body, and (b) a sample response
  shape for the non-obvious ones (health, auth tokens). No code changes, no
  new files, no dependencies.

### Risks & unknowns

- **Response bodies drift.** Sample JSON responses are a snapshot — if the
  schema changes, the doc goes stale. Mitigation: only show responses where
  they add real value (health status, auth token), and keep them short.
- **Auth flow assumption.** The examples assume the reader registers, copies
  the `access_token`, and exports it as `$TOKEN`. If someone skips that step
  the profile/review examples will 401 — but that's true of the API itself,
  not a doc bug.
- **File upload example.** `-F "resume_file=@./resume.pdf"` requires the user
  to actually have a `resume.pdf` on disk. Left as-is because it mirrors
  reality; a note could be added if it confuses testers.
- **OAuth2 form quirk.** `/auth/login` takes `username=<email>` because
  FastAPI's `OAuth2PasswordRequestForm` names the field `username` regardless
  of what it holds. Called this out explicitly in the doc so readers don't
  send `email=...` and get 401s.

### Edge cases

- **503 from `/health`.** Documented that the same JSON shape is returned
  with a 503 status when any dependency is down, so readers aren't surprised
  by a non-200.
- **Pending reviews.** `POST /reviews` returns `status: "pending"`
  immediately; the review isn't ready to read. Called out that
  `GET /reviews/{id}` should be polled until `status == "complete"`.
- **Optional profile fields.** All three fields on `POST /profiles`
  (`github_username`, `portfolio_url`, `resume_file`) are optional. The
  example shows all three, but the doc text notes they're optional so readers
  know they can omit any.
- **Pagination bounds.** `GET /reviews` clamps `page < 1` to `1` and
  `page_size` to `[1, 100]`. Documented the defaults and max so callers
  don't wonder why `page_size=500` silently becomes `20`.
