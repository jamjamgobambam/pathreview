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

`POST /profiles` — Create a profile with resume and GitHub username.
`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
