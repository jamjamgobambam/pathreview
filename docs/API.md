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
**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `github_username` | string | optional | max 255 characters |
| `portfolio_url` | string | optional | max 500 characters |
| `resume_file` | file | optional | must be `application/pdf`, `text/markdown`, or `text/plain` |

**Example request:**
```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@resume.pdf"
```

**Errors:**
- `422 Unprocessable Entity` — returned if `resume_file` is provided but is not a PDF, Markdown, or plain text file.


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
