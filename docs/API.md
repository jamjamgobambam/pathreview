# API Reference

Base URL: `http://localhost:8000`

## Authentication walkthrough

Every endpoint below except `GET /health` requires a JWT access token. Get one
by registering, then reuse it as a Bearer token on every subsequent request.

**1. Register** — plain JSON:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"password123"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
`200` on success. `400` if the email is already registered.

**2. Log in** — ⚠️ unlike every other endpoint here, `/auth/login` does **not**
accept JSON. It uses FastAPI's `OAuth2PasswordRequestForm`, so it requires a
form-encoded body with `username`/`password` fields (`username` holds the
email):

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=you@example.com&password=password123"
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
`200` on success. `401` on invalid credentials. Sending a JSON body here
returns `422 Unprocessable Entity` because `username`/`password` are missing
from the form data.

**3. Reuse the token** — save it and pass it as a Bearer token on every
protected request:

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl http://localhost:8000/profiles/{profile_id} \
  -H "Authorization: Bearer $TOKEN"
```

## Endpoints

### Health

`GET /health` — Returns service status and dependency health. No auth required.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-07-24T06:34:03.036433"
}
```
`200` if every dependency is healthy, `503` (with the same body shape, plus
whichever fields are `"unhealthy"`) if any dependency check fails.

> **Note:** in local dev you may see `postgres` reported as `"unhealthy"` here
> even though every DB-backed endpoint below works correctly. That's a known
> bug in the health check itself (`api/routes/health.py` runs a raw SQL string
> instead of a wrapped `text()` construct) — unrelated to this doc fix and
> tracked separately.

### Authentication

`POST /auth/register` — Create a new account. See the
[Authentication walkthrough](#authentication-walkthrough) above.

`POST /auth/login` — Obtain a JWT access token. See the
[Authentication walkthrough](#authentication-walkthrough) above — note the
form-encoded body requirement.

### Profiles

All `/profiles` endpoints require `Authorization: Bearer $TOKEN`.

`POST /profiles` — Create a profile with resume and GitHub username.

⚠️ This endpoint reads its fields via `Form(...)`/`File(...)`, so it's
**multipart**, not JSON — and unlike most validation errors, sending JSON
does **not** fail. It returns `200` with every field silently set to `null`.

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@resume.md;type=text/markdown"
```

```json
{
  "id": "dd24ef37-039d-4a24-b502-6e5d9fa6a784",
  "user_id": "b53806ed-2d22-4114-bff2-80d52a68ca49",
  "github_username": "octocat",
  "portfolio_url": "https://octocat.dev",
  "created_at": "2026-07-24T13:36:53.768862Z",
  "resume_filename": "resume.md"
}
```
`200` on success (all fields optional — you can omit any of them).

```bash
# JSON body instead of multipart: "succeeds" but silently drops every field
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_username":"octocat","portfolio_url":"https://example.com"}'
# -> 200 {"github_username":null,"portfolio_url":null,"resume_filename":null,...}
```

`422` if `resume_file` isn't PDF, Markdown, or plain text:
```json
{"detail":"Resume must be a PDF or Markdown file"}
```

> **Note:** PDF resumes currently always fail with
> `422 {"detail":"Failed to parse PDF resume"}` — the route imports
> `PyPDF2`, but the project depends on `pypdf` instead, so the import fails
> for every PDF upload. This is a bug unrelated to this doc fix; use a
> `.md` or `.txt` resume until it's addressed separately.

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl http://localhost:8000/profiles/{profile_id} \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "dd24ef37-039d-4a24-b502-6e5d9fa6a784",
  "user_id": "b53806ed-2d22-4114-bff2-80d52a68ca49",
  "github_username": "octocat",
  "portfolio_url": "https://octocat.dev",
  "created_at": "2026-07-24T13:36:53.768862Z",
  "resume_filename": "resume.md"
}
```
`200` on success. `401` with no/invalid token. `404` if the profile doesn't
exist or isn't owned by the current user.

`PUT /profiles/{profile_id}` — Update a profile's GitHub username and/or
portfolio URL. (Not in the original docs — confirmed working in the router.)

```bash
curl -X PUT http://localhost:8000/profiles/{profile_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_username":"octocat-updated","portfolio_url":"https://updated.example.com"}'
```

```json
{
  "id": "dd24ef37-039d-4a24-b502-6e5d9fa6a784",
  "user_id": "b53806ed-2d22-4114-bff2-80d52a68ca49",
  "github_username": "octocat-updated",
  "portfolio_url": "https://updated.example.com",
  "created_at": "2026-07-24T13:36:53.768862Z",
  "resume_filename": "resume.md"
}
```
`200` on success. Unlike `POST`, this endpoint takes plain JSON. `404` if
the profile doesn't exist or isn't owned by the current user.

`DELETE /profiles/{profile_id}` — Delete a profile and associated data
(cascades to reviews and ingested sources).

```bash
curl -X DELETE http://localhost:8000/profiles/{profile_id} \
  -H "Authorization: Bearer $TOKEN"
```
`204 No Content` on success (empty body). `404` if the profile doesn't exist
or isn't owned by the current user. A follow-up `GET` on the same ID then
returns `404`.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
