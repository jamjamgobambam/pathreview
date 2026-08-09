# API Reference

Base URL: `http://localhost:8000`

For convenience, the code examples below use environment variables. Set these in your terminal to easily copy and paste the commands:

```bash
export API_URL="http://localhost:8000"
export PROFILE_ID="<your-profile-id>"
export REVIEW_ID="<your-review-id>"
export TOKEN="<your-access-token>"
```

### Obtaining your credentials and IDs:

* **`TOKEN`**: Retrieve your access token by registering or logging in via the authentication endpoint.
* **`PROFILE_ID`** & **`REVIEW_ID`**: These values are returned in the JSON response payload after successfully creating a profile or a review.

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl "$API_URL/health"
```

Example response:

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-07-18T12:00:00.000000"
}
```

If any dependency is down, the endpoint returns `503 Service Unavailable` with `status: "unhealthy"` and the corresponding dependency marked `"unhealthy"`.

### Authentication

`POST /auth/register` — Create a new account.

```bash
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "a-strong-password"}'
```

`POST /auth/login` — Obtain a JWT access token.

This endpoint expects `application/x-www-form-urlencoded` data (OAuth2 password flow), not JSON. Pass your email as `username`:

```bash
curl -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=a-strong-password"
```

Both endpoints return the same shape on success:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save the token to reuse in later requests:

```bash
export TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -d "username=you@example.com&password=a-strong-password" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

### Profiles

All profile endpoints require an `Authorization: Bearer $TOKEN` header.

`POST /profiles` — Create a profile with resume and GitHub username.

This endpoint expects `multipart/form-data`, not JSON — `resume_file` must be PDF, Markdown, or plain text:

```bash
curl -X POST "$API_URL/profiles" \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://example.com" \
  -F "resume_file=@/path/to/resume.pdf"
```

Example response:

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "github_username": "octocat",
  "portfolio_url": "https://example.com",
  "created_at": "2026-07-31T12:00:00.000000",
  "resume_filename": "resume.pdf"
}
```

Save the returned `id` for later requests:

```bash
export PROFILE_ID="f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl "$API_URL/profiles/$PROFILE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Returns the same shape as above, or `404` if the profile doesn't exist or isn't owned by the current user.

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -X DELETE "$API_URL/profiles/$PROFILE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Returns `204 No Content` on success.

### Reviews

All review endpoints require an `Authorization: Bearer $TOKEN` header.

`POST /reviews` — Request a new portfolio review for a profile.

Ingestion and review generation run in the background — the response comes back immediately with `status: "pending"`.

```bash
curl -X POST "$API_URL/reviews" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"profile_id\": \"$PROFILE_ID\"}"
```

Example response:

```json
{
  "id": "9c858901-8a57-4791-81fe-4c455b099bc9",
  "profile_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-07-31T12:00:00.000000",
  "updated_at": "2026-07-31T12:00:00.000000"
}
```

Save the returned `id` to poll for the result:

```bash
export REVIEW_ID="9c858901-8a57-4791-81fe-4c455b099bc9"
```

`GET /reviews/{review_id}` — Retrieve a completed review.

```bash
curl "$API_URL/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $TOKEN"
```

`status` transitions from `"pending"` → `"processing"` → `"complete"` (or `"failed"`, with `error_message` set). Once complete, `sections`/`overall_score` are populated (`overall_score` is a 0–1 float):

```json
{
  "id": "9c858901-8a57-4791-81fe-4c455b099bc9",
  "profile_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "complete",
  "sections": [
    {
      "section_name": "Technical Skills",
      "content": "Detailed feedback on technical skills based on portfolio analysis",
      "confidence": 0.85,
      "suggestions": ["Add more detail on AI/ML experience", "Include specific technologies and frameworks"]
    }
  ],
  "overall_score": 0.81,
  "error_message": null,
  "created_at": "2026-07-31T12:00:00.000000",
  "updated_at": "2026-07-31T12:05:00.000000"
}
```

`GET /reviews` — List reviews for the authenticated user (paginated).

```bash
curl "$API_URL/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

Example response:

```json
{
  "items": [
    {
      "id": "9c858901-8a57-4791-81fe-4c455b099bc9",
      "profile_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "complete",
      "sections": [],
      "overall_score": 0.81,
      "error_message": null,
      "created_at": "2026-07-31T12:00:00.000000",
      "updated_at": "2026-07-31T12:05:00.000000"
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
