## Solution plan

**Issue:** #89 — API reference doc is missing the `POST /profiles` request body schema
https://github.com/ascherj/pathreview/issues/89

### Understand

**Root cause.** `docs/API.md` lists every endpoint as a single line — for example,
`` `POST /profiles` — Create a profile with resume and GitHub username. `` — with no
description of what a client must send. No content type, no field names, no
required/optional information, no example, and no mention that both POST endpoints
require an `Authorization: Bearer <token>` header (enforced by `get_current_user`
in `api/middleware/auth.py`).

**Expected behavior.** A developer reading `docs/API.md` should be able to build a
working request to `POST /profiles` and `POST /reviews` without opening the source.

**Actual behavior.** The two endpoints take *different* content types, and the doc
describes them with structurally identical one-line entries. Verified against the
running server through the OpenAPI UI:

- `POST /profiles` takes `multipart/form-data` — three fields, `github_username`,
  `portfolio_url`, and a file upload `resume_file` that the doc never names.
  Confirmed by a successful 200 response; evidence in the Week 8 section of `JOURNAL.md`.
- `POST /reviews` takes `application/json` with one required field, `profile_id`.

The natural assumption for a POST endpoint is JSON, so a reader following the doc
will send the wrong content type to `/profiles`.

**Scope note.** The issue body states that response schemas are already documented.
In `main` they are not — `docs/API.md` documents neither requests nor responses. My
fix covers request bodies only, matching the issue title. I will raise the
response-schema discrepancy in the issue thread rather than silently widen scope.

### Map

File I will change:

- `docs/API.md` — the only file modified. New "Request" subsections under the
  `Profiles` and `Reviews` headings.

Files I read as the source of truth (not modified):

- `api/routes/profiles.py` — `create_profile_endpoint`: the `Form`/`File`
  parameter declarations, the MIME allowlist (`application/pdf`, `text/markdown`,
  `text/plain`), and the 422 raised for other file types.
- `api/routes/reviews.py` — `create_review_endpoint`: takes `data: ReviewCreate`
  as a JSON body.
- `api/schemas/profile.py` — `ProfileCreate`: `github_username` (`max_length=255`),
  `portfolio_url` (`max_length=500`), both optional.
- `api/schemas/review.py` — `ReviewCreate`: `profile_id: UUID`, required.
- `api/middleware/auth.py` — `get_current_user`: the 401 path and the
  `WWW-Authenticate: Bearer` header both POST endpoints inherit.
- `docs/CONTRIBUTING.md` — branch naming, Conventional Commits, PR process.

### Plan

1. **Confirm the wire format for both endpoints.** Done — ran the API locally and
   exercised both endpoints through `localhost:8000/docs`; evidence recorded in
   the Week 8 section of `JOURNAL.md`.
2. **Verify the error paths** (done) so documented status codes are observed rather
   than guessed: no bearer token returns 401 "Not authenticated";
   an over-length `github_username` returns 500 "Failed to create profile"; a
   nonexistent `profile_id` on `/reviews` returns 500 "Failed to create review";
   and a `.docx` resume upload returns 422 "Resume must be a PDF or Markdown file".
   Evidence in the Week 8 section of `JOURNAL.md`.
3. **Write the `POST /profiles` request section in `docs/API.md`** — content type
   `multipart/form-data`, a field table covering `github_username` (string,
   optional, max 255), `portfolio_url` (string, optional, max 500), and
   `resume_file` (file, optional, PDF/Markdown/plain text), plus a `curl -F` example.
4. **Write the `POST /reviews` request section** — content type `application/json`,
   a field table with `profile_id` (UUID string, required), a JSON example body,
   and a matching `curl` example.
5. **Document authentication and error responses** for both endpoints: the bearer
   token from `POST /auth/login`, 401 for a missing or expired token, 422 for an
   unsupported resume file type.
6. **Verify and submit.** Re-run every documented example against the local server
   and confirm the responses match; check open PRs referencing #89 to avoid
   duplicate work; commit as `docs(api): document POST request bodies in API
   reference` and open a PR closing #89.

### Inputs & outputs

**Inputs to the fix:** the handler signatures in `api/routes/profiles.py` and
`api/routes/reviews.py`, the Pydantic field constraints in
`api/schemas/profile.py` and `api/schemas/review.py`, and the live OpenAPI schema
at `localhost:8000/openapi.json`.

**Outputs:** a modified `docs/API.md` containing two new request sections (field
tables plus verified examples) and a short authentication note. Documented for
`POST /profiles`: content type `multipart/form-data`, fields `github_username`,
`portfolio_url`, `resume_file`. For `POST /reviews`: content type
`application/json`, field `profile_id`.

**Not changed:** no source files, no function signatures, no API behavior. Nothing
under `api/` is touched, so no test changes; verification is running each
documented example against the local server and comparing the observed status code
and response body.

### Risks & unknowns

- **The issue title points at the wrong format.** It says "request body schema,"
  which implies JSON, but `create_profile_endpoint` in `api/routes/profiles.py`
  uses `Form()`/`File()`. I confirmed form-data against the running server, so I
  will document that and flag the discrepancy in the PR description so the reviewer
  can confirm the intent.
- **Undocumented field `resume_file`.** It exists in the handler but appears in
  neither the issue nor `ProfileCreate`. Unknown whether the maintainer considers
  it in scope; I will include it and call it out rather than quietly omit it.
- **Two endpoints return 500 for invalid client input.** Confirmed by testing: an
  over-length `github_username` returns 500 "Failed to create profile", and a
  nonexistent `profile_id` returns 500 "Failed to create review". In both cases the
  Pydantic `ValidationError` (or missing row) is swallowed by the handler's generic
  `except Exception` in `api/routes/profiles.py` and `api/routes/reviews.py` and
  re-raised as a 500; Swagger marks both as *Undocumented*. This looks like a bug,
  but fixing it is a code change outside #89. Risk: documenting 500 as if it were
  intended behavior. Mitigation — document what the API actually does today, flag
  the discrepancy in the PR, and suggest a separate issue for the error handling.
- **PDF is advertised but non-functional.** Verified: the type allowlist accepts
  `application/pdf` and the rejection message names PDF first, yet no PDF upload
  succeeds. Documenting "PDF or Markdown" without qualification would be
  misleading; documenting "Markdown only" would contradict the code's intent. My
  plan is to document the allowlist as written, add a short note that PDF parsing
  currently fails, and open a separate issue for the bug — but I want the
  maintainer's read on this before the PR, since it is a judgment call about what
  the reference doc should describe: intended behavior or current behavior.
- **Code/doc mismatch on allowed resume types.** The allowlist in
  `api/routes/profiles.py` includes `text/plain`, but the error message says "PDF
  or Markdown file". I will document observed behavior and note the inconsistency
  separately; changing the message is a code fix outside this issue.
- **Duplicate-work risk.** The cohort ledger shows many claims on #89. I will check
  open PRs referencing the issue before pushing.
- **Response schemas out of scope but arguably expected.** The issue body assumes
  they exist. If the maintainer wants them too, the diff roughly doubles; I will
  ask in the issue thread before starting Week 9 rather than guess.

### Edge cases

The documentation must cover these so a reader is not surprised:

1. **A JSON body sent to `POST /profiles`** — the endpoint expects form-data, so
   this fails; the docs must state the content type explicitly.
2. **`POST /profiles` with no fields at all** — every field is optional, so this
   succeeds and creates a profile with `resume_filename: null` (observed with
   `resume_file` left empty). The docs must not imply any field is required.
3. **A resume upload with an unsupported type such as `.docx`** — verified: 422
   with `{"detail": "Resume must be a PDF or Markdown file"}`. Worth contrasting
   with the two 500s below: this check raises `HTTPException` explicitly, so the
   handler's `except HTTPException: raise` branch passes it through intact.
4. **A PDF resume** — verified: *every* PDF returns 422 with
   `{"detail": "Failed to parse PDF resume"}`, while Markdown returns 200. The PDF
   branch in `create_profile_endpoint` passes raw `bytes` to `PyPDF2.PdfReader`,
   which needs a file-like object. Readers must be able to tell this failure apart
   from the wrong-file-type 422, which has a different detail string.
5. **A missing, malformed, or expired bearer token** — verified: 401 with
   `{"detail": "Not authenticated"}` and a `www-authenticate: Bearer` header.
6. **`github_username` longer than the 255-character limit** — verified: 500 with
   `{"detail": "Failed to create profile"}`, not the 422 a reader would expect.
7. **`POST /reviews` with a `profile_id` that does not exist** — verified: 500 with
   `{"detail": "Failed to create review"}`. The review is not created.
8. **`POST /reviews` with a valid, existing `profile_id`** — 200 with
   `status: "pending"`; the analysis runs in the background, so the docs must say
   the response is immediate and the result is not ready yet.