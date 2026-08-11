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

Requires an `Authorization: Bearer <token>` header. Request body is `multipart/form-data`, not JSON, since it accepts a file upload alongside form fields.

| Field | Type | Required | Description |
|---|---|---|---|
| `github_username` | string (form field, max 255 chars) | No | GitHub username to pull public repos from during review. |
| `portfolio_url` | string (form field, max 500 chars) | No | URL of an external portfolio site to include in the review. |
| `resume_file` | file | No | Resume upload. Must be `application/pdf`, `text/markdown`, or `text/plain` — other types return `422 Unprocessable Entity`. |

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

Requires an `Authorization: Bearer <token>` header. Request body is JSON. Returns the review immediately with `status: "pending"` and processes it asynchronously in the background.

| Field | Type | Required | Description |
|---|---|---|---|
| `profile_id` | UUID | Yes | ID of the profile to review. Must belong to the authenticated user. |

Example:

```json
{
  "profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
