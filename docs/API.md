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

**Request Body (multipart/form-data):**

| Field | Type | Required | Description |
|---|---|---|---|
| `github_username` | string | No | GitHub username to ingest public repositories and profile details. Max length 255. |
| `portfolio_url` | string | No | Personal portfolio site URL to scrape. Max length 500. |
| `resume_file` | file | No | Resume file to parse. Must be a PDF, Markdown (`.md`), or plain text (`.txt`) file. |

**Example Request:**
- `github_username`: `octocat`
- `portfolio_url`: `https://octocat.github.io`
- `resume_file`: (binary payload of `resume.pdf`)

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

**Request Body (application/json):**

| Field | Type | Required | Description |
|---|---|---|---|
| `profile_id` | string (UUID) | Yes | The ID of the profile to generate a review for. |

**Example Request Body:**
```json
{
  "profile_id": "c16297fe-1fc6-4d3e-824e-9e546bc37a8f"
}
```

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
