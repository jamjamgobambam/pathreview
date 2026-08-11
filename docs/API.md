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
`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

#### `POST /profiles` — request

**Content type:** `multipart/form-data` (not JSON)
**Authentication:** required — `Authorization: Bearer <token>` from `POST /auth/login`

| Field | Type | Required | Constraints | Description |
| --- | --- | --- | --- | --- |
| `github_username` | string | No | max 255 characters | GitHub handle to analyze. |
| `portfolio_url` | string | No | max 500 characters | URL of the developer's portfolio site. |
| `resume_file` | file | No | `application/pdf`, `text/markdown`, `text/plain` | Resume upload. See the PDF limitation below. |

All three fields are optional; a request with none of them creates an empty
profile with `resume_filename: null`.

```bash
curl -X POST 'http://localhost:8000/profiles' \
  -H 'Authorization: Bearer <token>' \
  -F 'github_username=daidai1031' \
  -F 'portfolio_url=https://example.com' \
  -F 'resume_file=@resume.md'
```

> **Known limitation:** although `application/pdf` is on the accepted-types list,
> PDF uploads currently fail with `422 {"detail": "Failed to parse PDF resume"}`.
> Markdown and plain text uploads succeed. Documented here as observed behavior;
> the underlying cause is a code defect outside the scope of this change.

**Error responses**

| Status | Body | Cause |
| --- | --- | --- |
| 401 | `{"detail": "Not authenticated"}` | Missing, malformed, or expired bearer token. Response carries `WWW-Authenticate: Bearer`. |
| 422 | `{"detail": "Resume must be a PDF or Markdown file"}` | `resume_file` has an unsupported content type. |
| 422 | `{"detail": "Failed to parse PDF resume"}` | PDF upload — see the limitation above. |
| 500 | `{"detail": "Failed to create profile"}` | `github_username` exceeds 255 characters. Returned as 500 rather than 422; documented as currently observed. |

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

#### `POST /reviews` — request

**Content type:** `application/json`
**Authentication:** required — `Authorization: Bearer <token>` from `POST /auth/login`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `profile_id` | string (UUID) | Yes | ID of an existing profile, as returned by `POST /profiles`. |

```json
{
  "profile_id": "39539042-b11e-4fa1-9f7a-068398cba5eb"
}
```

```bash
curl -X POST 'http://localhost:8000/reviews' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"profile_id": "39539042-b11e-4fa1-9f7a-068398cba5eb"}'
```

A successful request returns `200` immediately with `status: "pending"`; the
analysis runs in the background, so the review content is not yet available in
this response.

**Error responses**

| Status | Body | Cause |
| --- | --- | --- |
| 401 | `{"detail": "Not authenticated"}` | Missing, malformed, or expired bearer token. |
| 500 | `{"detail": "Failed to create review"}` | No profile matches `profile_id`. Returned as 500 rather than 404; documented as currently observed. |
## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
