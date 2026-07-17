# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

### Authentication

`POST /auth/register` — Create a new account.
`POST /auth/login` — Obtain a JWT access token.

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

**Request body:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `github_username` | string | No | GitHub username to associate with the profile (max 255 chars). |
| `portfolio_url` | string | No | URL to the user's portfolio site (max 500 chars). |
| `resume_file` | file | No | Resume upload. Must be PDF, Markdown, or plain text. Returns `422` for other file types. |

Example (`curl`):
```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@resume.pdf;type=application/pdf"
```

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

**Request body:** `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `profile_id` | UUID (string) | Yes | ID of the profile to review. Must belong to the authenticated user. |

Example:
```json
{
  "profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

Returns the review immediately with `status: "pending"`; ingestion and agent processing run asynchronously in the background.

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
