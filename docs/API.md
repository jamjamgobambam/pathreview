# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

### Authentication

`POST /auth/register` — Create a new account.
`POST /auth/login` — Obtain a JWT access token.

All profile and review endpoints require a bearer token. Obtain one from
`POST /auth/login`, which takes an `application/x-www-form-urlencoded` body with
`username` (your email address) and `password`:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=your-password"
```

The response is `{"access_token": "<token>", "token_type": "bearer"}`. Send the
token as `Authorization: Bearer <token>` on every request below. A missing,
malformed, or expired token returns `401`.

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

Content type: `multipart/form-data`. All fields are optional, so a request with
no fields creates an empty profile.

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `github_username` | string | No | Max 255 characters |
| `portfolio_url` | string | No | Max 500 characters |
| `resume_file` | file | No | PDF, Markdown, or plain text only |

The resume type is taken from the upload's content type, falling back to a guess
from the filename extension. Only `application/pdf`, `text/markdown`, and
`text/plain` are accepted; Markdown and plain text are read as UTF-8, and PDFs
are parsed for their text content.

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://octocat.example.com" \
  -F "resume_file=@resume.pdf;type=application/pdf"
```

Returns the created profile (`id`, `user_id`, `github_username`, `portfolio_url`,
`resume_filename`, `created_at`). Errors: `422` if `resume_file` is any other type
(`"Resume must be a PDF or Markdown file"`), `422` if a PDF cannot be parsed
(`"Failed to parse PDF resume"`), and `422` if a field exceeds its length limit.

`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

Content type: `application/json`.

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `profile_id` | UUID | Yes | ID of an existing profile you own |

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
```

Returns immediately with `status: "pending"`; ingestion and review generation run
in the background, so poll `GET /reviews/{review_id}` for the result. Errors:
`422` if `profile_id` is missing or is not a valid UUID. The endpoint does not
check that the profile exists before creating the review, so an unknown
`profile_id` fails the database foreign-key constraint and returns `500` rather
than `404`.

`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
