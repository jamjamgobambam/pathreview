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

Send as `multipart/form-data` with a Bearer token
(`Authorization: Bearer <token>`, obtained from `POST /auth/login`); requests
without a valid token return `401`. All fields are optional.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `github_username` | string | No | GitHub username. Max 255 characters. |
| `portfolio_url` | string | No | Portfolio URL. Max 500 characters. |
| `resume_file` | file | No | Resume upload. Must be PDF, Markdown, or plain text (`application/pdf`, `text/markdown`, `text/plain`); any other type returns `422` with `{"detail": "Resume must be a PDF or Markdown file"}`. |

Example:

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octo.dev" \
  -F "resume_file=@resume.pdf"
```

On success, returns `200` with the created profile (`id`, `user_id`,
`github_username`, `portfolio_url`, `created_at`, `resume_filename`).

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
