# API Reference

Base URL: `http://localhost:8000`

Most endpoints below require a JWT from `/auth/register` or `/auth/login`. Save it to a
shell variable so you can reuse it across the other examples:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=jane@example.com&password=hunter22" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

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
  "timestamp": "2026-08-04T17:32:10.123456"
}
```

### Authentication

`POST /auth/register` — Create a new account.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "hunter22"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

`POST /auth/login` — Obtain a JWT access token.

> Unlike the other endpoints, this one takes **form data**, not JSON — `username` is your
> email. Sending a JSON body here will fail with a 422.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=jane@example.com&password=hunter22"
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

> This is a **multipart** request, not JSON, because it accepts a file upload. Use `-F` for
> every field, including the non-file ones.

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=janedoe" \
  -F "portfolio_url=https://jane.dev" \
  -F "resume_file=@resume.md;type=text/markdown"
```

```json
{
  "id": "5b1f6c0a-2e3d-4b8a-9c1f-7a2e6d4b8f31",
  "user_id": "3a2b1c0d-9e8f-4a7b-8c6d-5e4f3a2b1c0d",
  "github_username": "janedoe",
  "portfolio_url": "https://jane.dev",
  "created_at": "2026-08-04T17:35:00.123456",
  "resume_filename": "resume.pdf"
}
```

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl http://localhost:8000/profiles/<profile_id> \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "5b1f6c0a-2e3d-4b8a-9c1f-7a2e6d4b8f31",
  "user_id": "3a2b1c0d-9e8f-4a7b-8c6d-5e4f3a2b1c0d",
  "github_username": "janedoe",
  "portfolio_url": "https://jane.dev",
  "created_at": "2026-08-04T17:35:00.123456",
  "resume_filename": "resume.pdf"
}
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -X DELETE http://localhost:8000/profiles/<profile_id> \
  -H "Authorization: Bearer $TOKEN"
```

Returns `204 No Content` with an empty body on success.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "<profile_id>"}'
```

```json
{
  "id": "8f4c2a91-6b3d-4e7a-9c5f-1a2b3c4d5e6f",
  "profile_id": "5b1f6c0a-2e3d-4b8a-9c1f-7a2e6d4b8f31",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-08-04T17:40:00.123456",
  "updated_at": "2026-08-04T17:40:00.123456"
}
```

`GET /reviews/{review_id}` — Retrieve a completed review.

```bash
curl http://localhost:8000/reviews/<review_id> \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "id": "8f4c2a91-6b3d-4e7a-9c5f-1a2b3c4d5e6f",
  "profile_id": "5b1f6c0a-2e3d-4b8a-9c1f-7a2e6d4b8f31",
  "status": "completed",
  "sections": [
    {
      "section_name": "project_quality",
      "content": "Your top repository shows solid test coverage but is missing a README with setup instructions.",
      "confidence": 0.87,
      "suggestions": ["Add a README with setup instructions", "Include a CI badge"]
    }
  ],
  "overall_score": 7.5,
  "error_message": null,
  "created_at": "2026-08-04T17:40:00.123456",
  "updated_at": "2026-08-04T17:42:30.654321"
}
```

`GET /reviews` — List reviews for the authenticated user (paginated).

```bash
curl "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "items": [
    {
      "id": "8f4c2a91-6b3d-4e7a-9c5f-1a2b3c4d5e6f",
      "profile_id": "5b1f6c0a-2e3d-4b8a-9c1f-7a2e6d4b8f31",
      "status": "completed",
      "sections": null,
      "overall_score": 7.5,
      "error_message": null,
      "created_at": "2026-08-04T17:40:00.123456",
      "updated_at": "2026-08-04T17:42:30.654321"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
