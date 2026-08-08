# API Reference

Base URL: `http://localhost:8000`

Every example below assumes the API is running locally (`make run`). Endpoints
under Profiles and Reviews require a JWT — get one from `/auth/register` or
`/auth/login` and pass it as `Authorization: Bearer $TOKEN`.

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl http://localhost:8000/health
```

Sample response:

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-07-25T12:00:00.000000"
}
```

Returns `503` with the same shape if any dependency is unhealthy.

### Authentication

`POST /auth/register` — Create a new account. Returns a JWT.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"correcthorsebatterystaple"}'
```

`POST /auth/login` — Obtain a JWT access token. Uses OAuth2 form-encoded body
(`username` holds the email).

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=correcthorsebatterystaple"
```

Both return:

```json
{"access_token": "eyJhbGciOi...", "token_type": "bearer"}
```

Export the token for the examples below:

```bash
export TOKEN="eyJhbGciOi..."
```

### Profiles

`POST /profiles` — Create a profile. Multipart form; `github_username`,
`portfolio_url`, and `resume_file` (PDF or Markdown) are all optional.

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@./resume.pdf"
```

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl http://localhost:8000/profiles/$PROFILE_ID \
  -H "Authorization: Bearer $TOKEN"
```

`PUT /profiles/{profile_id}` — Update `github_username` or `portfolio_url`.

```bash
curl -X PUT http://localhost:8000/profiles/$PROFILE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"portfolio_url":"https://new.example.com"}'
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -X DELETE http://localhost:8000/profiles/$PROFILE_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Reviews

`POST /reviews` — Request a new portfolio review for a profile. Returns
immediately with `status: "pending"`; processing runs in the background.

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"profile_id\":\"$PROFILE_ID\"}"
```

`GET /reviews/{review_id}` — Retrieve a review (poll until `status` is
`"complete"`).

```bash
curl http://localhost:8000/reviews/$REVIEW_ID \
  -H "Authorization: Bearer $TOKEN"
```

`GET /reviews/{review_id}/status` — Lightweight status/progress check.

```bash
curl http://localhost:8000/reviews/$REVIEW_ID/status \
  -H "Authorization: Bearer $TOKEN"
```

`GET /reviews` — List reviews for the authenticated user. Query params:
`page` (default `1`), `page_size` (default `20`, max `100`).

```bash
curl "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
