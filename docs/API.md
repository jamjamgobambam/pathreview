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

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).
`POST /reviews/{review_id}/share` — Create (or reuse) a public share link for a completed review you own. Returns `{ token, expires_at }`. Responds `404` if the review is not found or not yours, `409` if it is not complete.

### Share (public)

`GET /share/{token}` — **Unauthenticated.** Retrieve the read-only summary for a shared review. Returns `404` if the token is unknown or the link has expired (30 days after creation). Ownership fields are omitted from the response.

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
