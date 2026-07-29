# Solution Plan: Issue #117 - API docs don't include example `curl` commands

## Understand

`docs/API.md` currently lists a subset of PathReview's HTTP endpoints and links
to Swagger and ReDoc, but it does not show request formats, authentication, or
copy-paste terminal commands. A new contributor must inspect the generated
OpenAPI document or route code to learn that registration uses JSON, login uses
form fields, profile creation uses multipart form data, and profile/review
routes require a bearer token.

The route definitions also expose two public endpoints absent from the current
reference: `PUT /profiles/{profile_id}` and
`GET /reviews/{review_id}/status`. The documentation needs to reflect the full
public route surface rather than only adding examples to the existing partial
list.

**Root cause:** `docs/API.md` is a terse endpoint inventory, not an executable
API reference.

## Map

- `docs/API.md` - the API reference to expand with setup instructions, endpoint
  descriptions, and runnable `curl` examples.
- `api/routes/auth.py` - confirms JSON registration and form-encoded login
  fields named `username` and `password`.
- `api/routes/profiles.py` - confirms multipart profile creation, bearer
  authentication, and the create/read/update/delete route shapes.
- `api/routes/reviews.py` - confirms authenticated review creation, retrieval,
  pagination, and status polling.
- `api/routes/health.py` - confirms the unauthenticated health endpoint.

No backend route, schema, database, or frontend change is required.

## Implementation

1. Add a setup section defining `BASE_URL`, a repeatable demo account, and how
   to capture the login token in `TOKEN`. Use Python, which is already a project
   prerequisite, instead of adding a `jq` dependency.
2. Document a `curl -sS` command for every public route except the undocumented
   root endpoint: health; register and login; profile create, retrieve, update,
   and delete; review create, retrieve, status, and list.
3. Match each command to its FastAPI contract: JSON for registration, update,
   and review creation; `application/x-www-form-urlencoded` login fields;
   multipart `-F` fields for profile creation; and a bearer header on every
   profile and review request.
4. Capture returned profile and review UUIDs into `PROFILE_ID` and `REVIEW_ID`
   so the commands form a complete lifecycle. Keep resume upload optional and
   show the local-file form field separately, so no fixture file is required.
5. Explain that review creation is asynchronous and cleanup via profile deletion
   should run last because it cascades to associated reviews.

## Inputs and Expected Results

- `GET /health` returns dependency health without authentication.
- `POST /auth/register` accepts `{ "email", "password" }` and returns an
  access token.
- `POST /auth/login` accepts form `username` and `password` values and returns
  an access token captured as `TOKEN`.
- Authenticated profile calls return and consume `PROFILE_ID`; creation supports
  optional `github_username`, `portfolio_url`, and `resume_file` multipart
  fields.
- Authenticated review creation accepts `{ "profile_id": "<PROFILE_ID>" }`,
  returns a pending review, and exposes `REVIEW_ID` for retrieve/status calls.
- Authenticated review listing demonstrates `page` and `page_size`; profile
  deletion returns no response body and is the final cleanup action.

## Verification

1. Compare every documented method and path with `api.main.app.openapi()`.
2. Parse all Bash code blocks with `zsh -n` to catch quoting and substitution
   errors without making requests.
3. Run `git diff --check` to confirm clean Markdown whitespace.
4. With Docker running, start a fresh local backend and execute the documented
   lifecycle against it: health, register, login, profile create/read/update,
   review create/retrieve/status/list, and profile delete.
5. Run `make test-all` and `make check`; report existing unrelated failures
   separately from this documentation-only change.

## Risks and Edge Cases

- A stale server can advertise a different API contract than the current
  checkout. Verify against a freshly started process before using live results
  as proof.
- Login must remain form-encoded because FastAPI's `OAuth2PasswordRequestForm`
  does not accept the registration JSON payload.
- Profile creation must remain multipart even when no resume is supplied;
  documenting JSON here would cause a 422 response.
- The examples avoid a hard-coded email, so repeated runs do not fail with the
  existing-account 400 response.
