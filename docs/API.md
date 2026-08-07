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

Create a new profile with optional resume upload. Resume must be PDF or Markdown. Returns 422 if the file is not PDF or Markdown.

**Request body:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `github_username` | string | No | GitHub username to associate with the profile (max 255 characters) |
| `portfolio_url` | string | No | URL of the developer's portfolio site (max 500 characters) |
| `resume_file` | file | No | Resume file to upload; accepted formats: PDF (`application/pdf`), Markdown (`text/markdown`), or plain text (`text/plain`) |

**Example request:**

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=janedoe" \
  -F "portfolio_url=https://janedoe.dev" \
  -F "resume_file=@resume.pdf"
```

---

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

#### `POST /reviews`

Request a new portfolio review for a profile. Triggers the ingestion pipeline and agent orchestration asynchronously. Returns the review immediately with `status: "pending"`.

**Request body:** `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `profile_id` | string (UUID) | Yes | ID of the profile to review |

**Example request:**

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}'
```

---

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
