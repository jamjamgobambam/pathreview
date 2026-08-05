# API Reference

Base URL: `http://localhost:8000`

Prerequisites: Docker services running (`docker compose up -d`), migrations applied,
and seed data loaded (`make setup` or `make seed`). Seed login:

- Email: `user1@example.com`
- Password: `password1`

Pretty-print responses optionally with `| jq`.

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl -s http://localhost:8000/health
```

Note: You may receive HTTP 503 with a JSON body while postgres/redis probes are
unhealthy (known issues in the health route). A JSON response still confirms the
API process is reachable.

### Authentication

`POST /auth/register` — Create a new account.

JSON body: `email`, `password` (min 8 characters).

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@example.com","password":"password123"}'
```

`POST /auth/login` — Obtain a JWT access token.

Uses OAuth2 **form** fields (not JSON): `username` is the email, plus `password`.

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=password1"
```

Capture the token for later calls (requires `jq`):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=password1" \
  | jq -r .access_token)
```

### Profiles

Authenticated endpoints require `Authorization: Bearer $TOKEN`.

`POST /profiles` — Create a profile with resume and GitHub username.

Multipart form fields: optional `github_username`, `portfolio_url`, and
`resume_file` (PDF or Markdown).

```bash
curl -s -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://example.com" \
  -F "resume_file=@./resume.md;type=text/markdown"
```

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl -s http://localhost:8000/profiles/YOUR_PROFILE_UUID \
  -H "Authorization: Bearer $TOKEN"
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -s -X DELETE http://localhost:8000/profiles/YOUR_PROFILE_UUID \
  -H "Authorization: Bearer $TOKEN"
```

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

JSON body: `profile_id` (UUID from a create-profile response).

```bash
curl -s -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id":"YOUR_PROFILE_UUID"}'
```

`GET /reviews/{review_id}` — Retrieve a completed review.

```bash
curl -s http://localhost:8000/reviews/YOUR_REVIEW_UUID \
  -H "Authorization: Bearer $TOKEN"
```

`GET /reviews` — List reviews for the authenticated user (paginated).

```bash
curl -s "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
