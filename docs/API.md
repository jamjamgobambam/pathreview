# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl http://localhost:8000/health
```

Example response (`200 OK`):

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-08-05T12:00:00.000000"
}
```
Returns `503 Service Unavailable` if any dependency is down, with the same body showing which one is `"unhealthy"`.

### Authentication

`POST /auth/register` — Create a new account. Returns a JWT access token.

Password must be 8-128 characters. Returns `400` if the email is already registered.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@example.com", "password": "changeme123"}'
```

<br>
<br>

`POST /auth/login` — Obtain a JWT access token.

**Note:**
This endpoint expects form data (OAuth2 style), not JSON, and the email goes in the `username` field.

Returns `401` if credentials are invalid.

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=dev@example.com" \
  -d "password=changeme123"
```

Both Endpoints return a token:

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

All endpoints below require this token. Save it to a variable so the rest of the examples are copy-pasteable:

```bash
export TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=dev@example.com" -d "password=changeme123" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### Profiles

`POST /profiles` — Create a profile with an optional resume upload, GitHub username, and portfolio URL.

Expects **multipart form data**, and all fields are optional.

The resume must be a PDF or Markdown file (returns `422` otherwise).

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@resume.pdf"
```

Example response (`200 OK`):

```json
{
  "id": "3f0e8a1c-9b2d-4c5e-8f7a-1b2c3d4e5f6a",
  "user_id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "github_username": "octocat",
  "portfolio_url": "https://octocat.dev",
  "created_at": "2026-08-05T12:00:00.000000",
  "resume_filename": "resume.pdf"
}
```

Save the `id` from the response — you'll need it to request a review.

<br>
<br>

`GET /profiles/{profile_id}` — Retrieve a profile. 

Returns `404` if not found or not owned by the authenticated user.

```bash
curl http://localhost:8000/profiles/3f0e8a1c-9b2d-4c5e-8f7a-1b2c3d4e5f6a \
  -H "Authorization: Bearer $TOKEN"
```

<br>
<br>

`PUT /profiles/{profile_id}` — Update a profile's GitHub username and/or portfolio URL (JSON body).

Returns `404` if not found or not owned by you.

```bash
curl -X PUT http://localhost:8000/profiles/3f0e8a1c-9b2d-4c5e-8f7a-1b2c3d4e5f6a \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_username": "octocat", "portfolio_url": "https://new.octocat.dev"}'
```

<br>
<br>

`DELETE /profiles/{profile_id}` — Delete a profile and associated reviews and ingested data.

Returns `204 No Content` on success.

```bash
curl -X DELETE http://localhost:8000/profiles/3f0e8a1c-9b2d-4c5e-8f7a-1b2c3d4e5f6a \
  -H "Authorization: Bearer $TOKEN"
```

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

Processing runs asynchronously — the response comes back immediately with `"status": "pending"`.

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "3f0e8a1c-9b2d-4c5e-8f7a-1b2c3d4e5f6a"}'
```

Example response (`200 OK`):

```json
{
  "id": "9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
  "profile_id": "3f0e8a1c-9b2d-4c5e-8f7a-1b2c3d4e5f6a",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-08-05T12:00:00.000000",
  "updated_at": "2026-08-05T12:00:00.000000"
}
```

<br>
<br>

`GET /reviews/{review_id}/status` — Poll status and progress while a review is processing. 

```bash
curl http://localhost:8000/reviews/9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d/status \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "review_id": "9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
  "status": "processing",
  "progress_pct": 40
}
```

<br>
<br>

`GET /reviews/{review_id}` — Retrieve a completed review.

Once completed, `sections` contains the feedback and `overall_score` is populated.

Returns `404` if not found or not owned by the authenticated user.

```bash
curl http://localhost:8000/reviews/9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d \
  -H "Authorization: Bearer $TOKEN"
```

<br>
<br>

`GET /reviews` — List reviews for the authenticated user (paginated).

`page` defults to 1, `page_size` defaults to 20 (max 100).

```bash
curl "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

Example response (`200 OK`):

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
