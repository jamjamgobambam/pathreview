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

**Request body** (`multipart/form-data`):

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `github_username` | string | No | Max length 255. **Known bug:** exceeding this returns `500 Internal Server Error` (`"Failed to create profile"`) instead of a `422` — see note below. |
| `portfolio_url` | string | No | Max length 500. Subject to the same known bug as `github_username` above. |
| `resume_file` | file | No | Accepted types: `application/pdf`, `text/markdown`, `text/plain`. Returns `422` with `"Resume must be a PDF or Markdown file"` for other types. |

> **Note:** Unlike `github_username` and `portfolio_url`, the `resume_file` type check isn't enforced by a Pydantic schema — it's a manual check inside `create_profile_endpoint` in `api/routes/profiles.py`. This means the accepted file types won't show up in the OpenAPI schema/Swagger UI's generated types; they're only enforced (and documented) here.
> **Known bug:** `github_username`/`portfolio_url` values exceeding their max length are rejected internally by Pydantic validation, but the endpoint doesn't catch this as an `HTTPException`, so it surfaces as a `500 Internal Server Error` rather than a `422`. Not yet filed as its own issue — documented here as-observed; fixing the endpoint's error handling is out of scope for this doc-only PR.

**Example request:**

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <access_token>" \
  -F "github_username=janedoe" \
  -F "portfolio_url=https://janedoe.dev" \
  -F "resume_file=@resume.pdf;type=application/pdf"
```

**Example response** (`200 OK`):

```json
{
  "id": "ad67c8b8-a40d-445e-bcca-fd03817dd168",
  "user_id": "a2501333-6997-45e5-9c7b-ecc45a221750",
  "github_username": "janedoe",
  "portfolio_url": "https://janedoe.dev",
  "created_at": "2026-07-31T04:21:59.448547Z",
  "resume_filename": "resume.pdf"
}
```

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
