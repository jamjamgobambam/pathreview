# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

### Authentication

`POST /auth/register` — Create a new account.
`POST /auth/login` — Obtain a JWT access token.

### Profiles

#### `POST /profiles`

Create a profile with resume and GitHub username.

**Authentication:** Required (JWT Bearer token)

**Content-Type:** `multipart/form-data`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `github_username` | string | No | GitHub username for profile. Max 255 characters. |
| `portfolio_url` | string | No | Portfolio website URL. Max 500 characters. |
| `resume_file` | file | No | Resume file upload. Must be PDF (`.pdf`) or Markdown (`.md`) format. |

**Validation:**
- At least one field should be provided (all fields are optional, but submitting no data creates an empty profile)
- `resume_file` must be PDF (`application/pdf`) or Markdown (`text/markdown`, `text/plain`) format
- Returns `422 Unprocessable Entity` if file format is invalid or PDF parsing fails

**Example Request:**

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "github_username=johndoe" \
  -F "portfolio_url=https://johndoe.dev" \
  -F "resume_file=@/path/to/resume.pdf"
```

**Response:** `200 OK`

Returns a `ProfileResponse` object with the created profile.

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "github_username": "johndoe",
  "portfolio_url": "https://johndoe.dev",
  "resume_filename": "resume.pdf",
  "created_at": "2026-07-22T10:30:00Z"
}
```

---

#### `GET /profiles/{profile_id}`

Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

#### `POST /reviews`

Request a new portfolio review for a profile. The review is processed asynchronously in the background.

**Authentication:** Required (JWT Bearer token)

**Content-Type:** `application/json`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile_id` | string (UUID) | Yes | The UUID of the profile to review. Must belong to the authenticated user. |

**Example Request:**

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

**Response:** `200 OK`

Returns a `ReviewResponse` object with `status="pending"`. The review will be processed asynchronously.

```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "profile_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-07-22T10:35:00Z",
  "updated_at": "2026-07-22T10:35:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Profile not found or doesn't belong to the authenticated user
- `422 Unprocessable Entity` - Invalid profile_id format (must be valid UUID)

---

#### `GET /reviews/{review_id}`

Retrieve a completed review.

#### `GET /reviews`

List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
