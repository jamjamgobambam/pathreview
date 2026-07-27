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

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Reproduction note (issue #117)

The following endpoints are implemented in the codebase but not yet documented
above:

- `PUT /profiles/{profile_id}` — Update a profile's github_username or portfolio_url. Requires auth.
- `GET /reviews/{review_id}/status` — Get review status and progress percentage. Requires auth.

Additionally, none of the endpoints above include example `curl` invocations.
A developer following this doc must read the route source in `api/routes/` to
discover request body shapes, which fields are required, and that
`POST /auth/login` uses OAuth2 form data (not JSON). This note documents the
gap; curl examples for all 11 endpoints will be added in the fix commit.

Verified locally: all endpoints function correctly when called with the right
request shape. Reproduction steps:
1. Run `make run` with Docker services healthy
2. Attempt `POST /auth/login` with JSON body — receive 422 (undocumented gotcha)
3. Open `docs/API.md` — no examples exist to clarify the correct format
