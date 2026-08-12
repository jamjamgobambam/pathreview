# API Reference

Base URL: `http://localhost:8000`

The examples below use `curl`, Python, and a shell that supports `export` (such
as macOS/Linux shells or Git Bash on Windows). Start the application with
`make run` before running them.

## Setup

Set values used by the examples. The timestamp keeps the registration example
repeatable without colliding with an existing account.

```bash
export BASE_URL="http://localhost:8000"
export DEMO_EMAIL="curl-demo-$(date +%s)@example.com"
export DEMO_PASSWORD="password123"
```

All profile and review endpoints require a bearer token. The login example
below saves it in `TOKEN`; the profile and review creation commands save their
returned identifiers in `PROFILE_ID` and `REVIEW_ID`.

## Health

### `GET /health`

Returns service and dependency health. It does not require authentication.

```bash
curl -sS "$BASE_URL/health"
```

## Authentication

### `POST /auth/register`

Creates an account and returns a bearer access token. Registration accepts a
JSON body with an email address and a password of at least eight characters.

```bash
curl -sS -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEMO_EMAIL\",\"password\":\"$DEMO_PASSWORD\"}"
```

### `POST /auth/login`

Obtains a bearer access token. This endpoint uses form fields named `username`
and `password`, not a JSON request body. The command stores the returned token
for the authenticated examples below.

```bash
export TOKEN="$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=$DEMO_EMAIL" \
  --data-urlencode "password=$DEMO_PASSWORD" \
  | python -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')"
```

## Profiles

### `POST /profiles`

Creates a profile. Profile fields are submitted as multipart form data; a
resume upload is optional. The command stores the new profile ID for later
requests.

```bash
export PROFILE_ID="$(curl -sS -X POST "$BASE_URL/profiles" \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://example.com/portfolio" \
  | python -c 'import json, sys; print(json.load(sys.stdin)["id"])')"
```

To include a resume, add a form field such as
`-F "resume_file=@/absolute/path/to/resume.pdf;type=application/pdf"` to the
creation request. Markdown and plain-text files are also accepted.

### `GET /profiles/{profile_id}`

Retrieves a profile owned by the authenticated user.

```bash
curl -sS "$BASE_URL/profiles/$PROFILE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### `PUT /profiles/{profile_id}`

Updates the supplied profile fields. Omit any field that should remain
unchanged.

```bash
curl -sS -X PUT "$BASE_URL/profiles/$PROFILE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_username":"octocat","portfolio_url":"https://example.com/updated-portfolio"}'
```

### `DELETE /profiles/{profile_id}`

Deletes a profile and its associated reviews and ingested data. Run this as the
final cleanup step; a successful response has no body.

```bash
curl -sS -X DELETE "$BASE_URL/profiles/$PROFILE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -o /dev/null -w "%{http_code}\\n"
```

## Reviews

### `POST /reviews`

Requests a portfolio review for a profile. Review processing runs in the
background, so the initial response has `status` set to `pending`. The command
stores the new review ID for the following requests.

```bash
export REVIEW_ID="$(curl -sS -X POST "$BASE_URL/reviews" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"profile_id\":\"$PROFILE_ID\"}" \
  | python -c 'import json, sys; print(json.load(sys.stdin)["id"])')"
```

### `GET /reviews/{review_id}`

Retrieves the review and its completed feedback when processing has finished.

```bash
curl -sS "$BASE_URL/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### `GET /reviews/{review_id}/status`

Retrieves the review's current status and progress percentage while it is being
processed.

```bash
curl -sS "$BASE_URL/reviews/$REVIEW_ID/status" \
  -H "Authorization: Bearer $TOKEN"
```

### `GET /reviews`

Lists reviews owned by the authenticated user. `page` defaults to `1` and
`page_size` defaults to `20`; the API accepts page sizes up to `100`.

```bash
curl -sS "$BASE_URL/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
