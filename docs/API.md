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

Request body (`multipart/form-data`):

| Field | Type | Required | Description |
|---|---|---|---|
| `github_username` | string | No | GitHub username to pull public repos from. |
| `portfolio_url` | string | No | URL of the user's portfolio site, max 500 characters. |
| `resume_file` | file | No | Resume upload. Must be `application/pdf`, `text/markdown`, or `text/plain`; returns 422 otherwise. |

Example (`curl`):
```
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@resume.pdf"
```

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

Request body (JSON):

| Field | Type | Required | Description |
|---|---|---|---|
| `profile_id` | UUID | Yes | ID of the profile to review. |

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
