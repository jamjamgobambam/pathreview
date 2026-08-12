# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

**Example:**

```bash
curl -X GET http://localhost:8000/health
```

**Expected Response:**

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-08-04T00:00:00.000000"
}
```

### Authentication

`POST /auth/register` — Create a new account.

**Example:**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'
```

**Expected Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

`POST /auth/login` — Obtain a JWT access token.

> **Note:** This endpoint uses OAuth2 form-data format (not JSON).

**Example:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=password1"
```

**Expected Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

> **Note:** This endpoint requires a JWT token. First login to get a token, then include it in the `Authorization` header.

**Example:**

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "github_username=octocat" \
  -F "resume=@/path/to/resume.pdf"
```

**Expected Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "github_username": "octocat",
  "portfolio_url": null,
  "created_at": "2026-08-04T00:00:00.000000",
  "resume_filename": "resume.pdf"
}
```

`GET /profiles/{profile_id}` — Retrieve a profile.

> **Note:** This endpoint requires a JWT token. Replace `{profile_id}` with the UUID from the profile you created.

**Example:**

```bash
curl -X GET http://localhost:8000/profiles/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "github_username": "octocat",
  "portfolio_url": null,
  "created_at": "2026-08-04T00:00:00.000000",
  "resume_filename": "resume.pdf"
}
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

> **Note:** This endpoint requires a JWT token. Replace `{profile_id}` with the UUID of the profile you want to delete.

**Example:**

```bash
curl -X DELETE http://localhost:8000/profiles/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:** `204 No Content`

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

> **Note:** This endpoint requires a JWT token. Replace `{profile_id}` with the UUID of the profile you want to review.

**Example:**

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "123e4567-e89b-12d3-a456-426614174000"}'
```

**Expected Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "profile_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-08-04T00:00:00.000000",
  "updated_at": "2026-08-04T00:00:00.000000"
}
```

`GET /reviews/{review_id}` — Retrieve a completed review.

> **Note:** This endpoint requires a JWT token. Replace `{review_id}` with the UUID of the review you want to retrieve.

**Example:**

```bash
curl -X GET http://localhost:8000/reviews/123e4567-e89b-12d3-a456-426614174002 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "profile_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "complete",
  "sections": [
    {
      "section_name": "Technical Skills",
      "content": "Your GitHub profile shows strong proficiency in Python...",
      "confidence": 0.82,
      "suggestions": ["Add a detailed README..."]
    }
  ],
  "overall_score": 0.74,
  "error_message": null,
  "created_at": "2026-08-04T00:00:00.000000",
  "updated_at": "2026-08-04T00:00:00.000000"
}
```

`GET /reviews` — List reviews for the authenticated user (paginated).

> **Note:** This endpoint requires a JWT token. You can customize the page and page size with query parameters.

**Example:**

```bash
curl -X GET "http://localhost:8000/reviews?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**

```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "profile_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "complete",
      "sections": ["..."],
      "overall_score": 0.74,
      "error_message": null,
      "created_at": "2026-08-04T00:00:00.000000",
      "updated_at": "2026-08-04T00:00:00.000000"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

## Interactive Docs

When the API is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

