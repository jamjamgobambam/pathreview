# API Reference

<!--
Reproduction note (issue #117): I ran the app locally with make run and hit these
endpoints from the terminal. Every endpoint below only gives me a method and a path,
no example request. For POST /auth/login I had to open api/routes/auth.py to find out
it expects OAuth2 form fields (username/password), not JSON, which isn't something I
could have guessed from this doc alone. For POST /profiles I had to check
api/routes/profiles.py to learn it's multipart form data with a resume_file upload, not
JSON either. This confirms the gap: a new contributor has no way to verify the API
works without reading route source files first.
-->

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

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
