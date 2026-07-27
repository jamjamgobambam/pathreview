# PLAN — Issue #89: Document the `POST /profiles` request body

## What needs to change

The API reference `docs/API.md` documents `POST /profiles` (line 18) as a single
sentence with **no request body schema**. A developer reading only this doc cannot
build a valid request: they don't know it is a `multipart/form-data` upload, which
fields exist, the field constraints, the allowed resume file types, or that a Bearer
token is required.

**A correct fix** adds a request body section for `POST /profiles` to `docs/API.md`
that states the content type, the auth requirement, a field-by-field table (name,
type, required, constraints), the resume file-type rule, and a runnable `curl`
example — so the doc alone is enough to call the endpoint correctly. This is a
documentation-only change; no application code changes.

## Reproduction (confirmed in the local environment)

Brought the stack up: `docker compose up -d` (Postgres + Redis healthy; Chroma not
needed here), `alembic upgrade head`, seeded users, then `uvicorn api.main:app` on
:8000. Exercised the real endpoint with `curl`, using a token from `POST /auth/login`
(seeded `user1@example.com` / `password1`):

| Request | Result | Confirms |
| --- | --- | --- |
| No token | `401` | Auth (Bearer token) is required |
| Token + `.png` file | `422` `{"detail":"Resume must be a PDF or Markdown file"}` | File-type rule + exact error message |
| Token + `github_username` = 300 chars | `500` `{"detail":"Failed to create profile"}` | Over-length is not a clean 422 (see risks) |
| Token + valid `github_username` + `portfolio_url` | `200` + profile JSON | Happy path |

The live OpenAPI (`/openapi.json`) declares the body as `multipart/form-data` with
`github_username`, `portfolio_url`, `resume_file`, and `security: OAuth2PasswordBearer`
— none of which appears in `docs/API.md`. The OpenAPI is itself thin: it omits the
length limits, the allowed file types, and the exact error messages, so the written
doc adds real value over "just read Swagger."

## Files involved

**Changed by the fix (one file):**
- `docs/API.md` — add the request body section under the `POST /profiles` line (line 18).

**Read-only, source of truth (not changed):**
- `api/routes/profiles.py` — `create_profile_endpoint` (lines 23–108); the
  `Form(...)`/`File(...)` signature (lines 24–30) and the file-type check (lines 42–53).
- `api/schemas/profile.py` — `ProfileCreate` (lines 7–9, the `max_length` limits) and
  `ProfileResponse` (lines 17–25, the success payload).

## Inputs and outputs (the contract being documented)

The fix does not change these — it documents them accurately.

**Inputs** — `multipart/form-data`, all fields optional, plus an auth header:
| Field | Type | Required | Constraint |
| --- | --- | --- | --- |
| `github_username` | string (form) | No | max 255 chars |
| `portfolio_url` | string (form) | No | max 500 chars |
| `resume_file` | file upload | No | must be `application/pdf`, `text/markdown`, or `text/plain` |
| `Authorization` header | `Bearer <token>` | Yes | from `POST /auth/login` |

**Outputs:**
- `200 OK` → `ProfileResponse` JSON: `id` (UUID), `user_id` (UUID),
  `github_username` (string\|null), `portfolio_url` (string\|null),
  `created_at` (datetime), `resume_filename` (string\|null).
- `401 Unauthorized` → missing/invalid token.
- `422 Unprocessable Entity` → disallowed resume file type, detail
  `"Resume must be a PDF or Markdown file"`.

## Sub-tasks (in order)

1. In `docs/API.md`, under the `POST /profiles` line, add a note: content type is
   `multipart/form-data` and a Bearer token is required (401 if missing).
2. Add the request field table (`github_username`, `portfolio_url`, `resume_file`)
   with columns Field / Type / Required / Description, including the length limits
   and allowed file types.
3. Add a one-line note on the resume file rule: the accepted types and the exact
   `422` detail returned for anything else.
4. Add a copy-pasteable `curl` example: base URL `http://localhost:8000`, a
   `Authorization: Bearer <token>` header, and `-F` form fields including a file upload.
5. Leave every other endpoint untouched and keep the file's existing terse style.
6. Run the verification steps below, then commit and push.

## Edge cases the documentation must cover

1. **Disallowed resume type** (e.g. `.png`, `.docx`): endpoint returns `422` with
   detail `"Resume must be a PDF or Markdown file"` — the doc must state the accepted
   types and this response.
2. **No fields at all / a single field**: every field is optional, so a request with
   only `github_username` (or nothing) still returns `200` — the doc must mark each
   field optional, not imply any is required.
3. **Missing or expired token**: returns `401` — the doc must state auth is required
   and point to `POST /auth/login`.
4. **`text/plain` resume**: accepted even though the error message names only "PDF or
   Markdown" — the doc must list plain text as an accepted type.

## Risks / unknowns (each tied to a concrete location)

- **Over-length values return 500, not 422.** `max_length` (255/500) is declared on
  `ProfileCreate` in `api/schemas/profile.py:7-9`, but the model is constructed
  *after* form parsing in `api/routes/profiles.py:79-82`, so an over-long value throws
  and surfaces as `500 {"detail":"Failed to create profile"}`. Decision: document the
  limits as the intended constraints, but do **not** claim a 422 for exceeding them.
  This is a latent bug, **out of scope for #89** — raise a separate issue.
- **File-type message is narrower than the rule.** The check in
  `api/routes/profiles.py:42-53` accepts `text/plain`, but its message says only
  "PDF or Markdown." Document the true accepted set and quote the exact message.
- **Scope creep.** The manifest E-14 text also names `POST /reviews`, but issue #89's
  title is `POST /profiles` only (see `docs/API.md:24` for the reviews line). Plan
  stays profiles-only; a reviewer may ask for reviews too — easy to add later.
- **New formatting convention.** This is the first request-body block in `docs/API.md`;
  keep it clean so it can be reused for other endpoints.

## Incidental findings (NOT part of this issue)

- `GET /health` returns `503` due to bugs in the health-check code itself, not real
  outages: the Postgres check uses a bare `SELECT 1` (SQLAlchemy 2.x needs
  `text('SELECT 1')`) and the Redis check reads a non-existent `settings.redis_host`.
  The app otherwise runs fine. Worth a separate issue; not touching here.

## Verification

- Re-read `docs/API.md`; confirm the table and `curl` block render as valid GitHub markdown.
- Cross-check every documented field, constraint, and status code against the
  reproduction table above and `api/routes/profiles.py`.
- With the app running at `http://localhost:8000`, open `/docs` and confirm the
  Swagger `POST /profiles` body matches the doc.
- Commit the fix as `docs(api): add POST /profiles request body schema` with
  `Fixes #89` in the body; push to `origin`; open a PR into `ascherj/main`.
