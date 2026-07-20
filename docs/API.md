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

#### `POST /profiles` request body

Content type: `multipart/form-data`

| Field | Type | Required | Description | Example |
| --- | --- | --- | --- | --- |
| `github_username` | string | No | GitHub username, up to 255 characters. | `octocat` |
| `portfolio_url` | string | No | Portfolio URL, up to 500 characters. | `https://octocat.example.com` |
| `resume_file` | file | No | Resume in PDF, Markdown, or plain-text format. | `resume.pdf` |

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

#### `POST /reviews` request body

Content type: `application/json`

| Field | Type | Required | Description | Example |
| --- | --- | --- | --- | --- |
| `profile_id` | UUID | Yes | ID of the profile to review. | `550e8400-e29b-41d4-a716-446655440000` |

Example:

```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
