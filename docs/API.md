# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

Example:

```sh
curl http://localhost:8000/health
```

### Authentication

`POST /auth/register` — Create a new account.

Example:

```sh
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

`POST /auth/login` — Obtain a JWT access token.

Example:

```sh
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

Example:

```sh
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "github_username=example-user" \
  -F "portfolio_url=https://example.com" \
  -F "resume_file=@resume.pdf"
```

`GET /profiles/{profile_id}` — Retrieve a profile.

Example:

```sh
curl http://localhost:8000/profiles/PROFILE_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

Example:

```sh
curl -X DELETE http://localhost:8000/profiles/PROFILE_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

Example:

```sh
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "PROFILE_ID"
  }'
```

`GET /reviews/{review_id}` — Retrieve a completed review.

Example:

```sh
curl http://localhost:8000/reviews/REVIEW_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

`GET /reviews` — List reviews for the authenticated user (paginated).

Example:

```sh
curl "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc -->
