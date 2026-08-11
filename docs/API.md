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

### Webhooks

`POST /webhooks/callbacks` — Register a callback URL to be notified when a profile's review
completes. Only one callback is allowed per profile; returns `409` if one is already registered,
or `404` if the profile doesn't exist or isn't owned by the authenticated user.
`DELETE /webhooks/callbacks/{profile_id}` — Delete the callback registered for a profile.

See [Client Callback Setup](examples/CLIENT_CALLBACK_SETUP.md) for a runnable end-to-end walkthrough.

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
