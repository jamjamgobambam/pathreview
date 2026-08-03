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

Request body: `multipart/form-data` (not JSON), since the resume is uploaded as a file.

| Field | Type | Required | Notes |
|---|---|---|---|
| `github_username` | string (max 255 chars) | No | GitHub handle to associate with the profile |
| `portfolio_url` | string (max 500 chars) | No | Link to an external portfolio site |
| `resume_file` | file | No | Must be `application/pdf`, `text/markdown`, or `text/plain`. Returns `422` if the file type doesn't match |

Example (curl):
```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.dev" \
  -F "resume_file=@resume.pdf"
```

Response body:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `user_id` | UUID | |
| `github_username` | string \| null | |
| `portfolio_url` | string \| null | |
| `resume_filename` | string \| null | Original filename of the uploaded resume, if any |
| `created_at` | datetime | |

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

Request body: `application/json`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `profile_id` | UUID | Yes | ID of the profile to review |

Example:
```json
{
  "profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

The review is created with `status: "pending"` and returned immediately; the actual analysis (ingestion + agent orchestration) runs as a background task. Poll `GET /reviews/{review_id}` or `GET /reviews/{review_id}/status` to check progress.

Response body:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `profile_id` | UUID | |
| `status` | string | `"pending"`, `"processing"`, `"complete"`, or `"failed"` |
| `sections` | array \| null | List of `{section_name, content, confidence, suggestions}` objects; `null` until processing finishes |
| `overall_score` | number \| null | |
| `error_message` | string \| null | Populated if processing failed |
| `created_at` | datetime | |
| `updated_at` | datetime | |

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
