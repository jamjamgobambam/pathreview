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
<!--
REPRODUCTION NOTE (Issue #89):
The request body schema for POST /profiles is missing from this documentation.
Based on api/routes/profiles.py:24-30 and api/schemas/profile.py:7-10, this endpoint accepts:
- github_username: Optional[str] (Form field, max 255 chars)
- portfolio_url: Optional[str] (Form field, max 500 chars)
- resume_file: Optional[UploadFile] (File upload, must be PDF or Markdown)

This documentation gap makes it difficult for frontend developers to know what parameters
are required/accepted when creating a profile.
-->
`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
<!--
REPRODUCTION NOTE (Issue #89):
The request body schema for POST /reviews is also missing from this documentation.
Based on api/routes/reviews.py:22-28 and api/schemas/review.py:14-15, this endpoint accepts:
- profile_id: UUID (required field in JSON body)
-->
`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
