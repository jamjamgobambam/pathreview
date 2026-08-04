# API Reference
Base URL: `http://localhost:8000`
Interactive docs (when the app is running):
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
---
## Authentication
Most endpoints require a Bearer token. Obtain one by registering a new account
or logging in with an existing one. Pass the token in every authenticated request:
```
Authorization: Bearer <your-token>
```
Endpoints that require authentication are marked with 🔒.
---
## Endpoints
### Health
#### `GET /health` — Service and dependency health check
No authentication required.
```bash
curl -s http://localhost:8000/health
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-07-28T03:41:40.773184"
}
```
> **Note:** In some local environments this endpoint may report `postgres` or
> `redis` as `"unhealthy"` even when the app is functioning correctly. This is
> a known issue with the health check's Redis connection logic — it reads
> `redis_host` and `redis_port` as separate settings that do not exist in
> `core/config.py`, which only defines `redis_url`. If register, login, and
> profile endpoints respond normally, the app is working. Confirm container
> status with `docker compose ps`.
---
### Authentication
#### `POST /auth/register` — Create a new account
No authentication required. Returns a JWT access token on success.
```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```
**Response (200 OK):**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```
Save the `access_token` — pass it as `Authorization: Bearer <token>` in all
authenticated requests. Returns 400 if the email is already registered.
---
#### `POST /auth/login` — Obtain a JWT access token
No authentication required.
> **Important:** This endpoint uses OAuth2 form data, **not JSON**. Use `-F`
> flags instead of `-d` with `Content-Type: application/json` — sending JSON
> returns 422 Unprocessable Entity.
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -F "username=you@example.com" \
  -F "password=yourpassword"
```
**Response (200 OK):**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```
Returns 401 if credentials are invalid or the account is inactive.
---
### Profiles
#### `POST /profiles` — Create a profile 🔒
Requires authentication. Accepts **multipart form data** (not JSON) — use `-F`
flags. Resume file is optional; if provided, must be PDF or Markdown.
```bash
curl -s -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <your-token>" \
  -F "github_username=your-github-handle" \
  -F "portfolio_url=https://yoursite.io"
```
To include a resume file:
```bash
curl -s -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <your-token>" \
  -F "github_username=your-github-handle" \
  -F "portfolio_url=https://yoursite.io" \
  -F "resume_file=@/path/to/resume.pdf"
```
**Response (200 OK):**
```json
{
  "id": "4af2e07d-857c-4754-b246-735d26abcc33",
  "user_id": "c6a8a47e-8b2f-48e8-8b77-eb9c6a3931df",
  "github_username": "your-github-handle",
  "portfolio_url": "https://yoursite.io",
  "created_at": "2026-07-28T03:54:20.780690Z",
  "resume_filename": null
}
```
Save the `id` — you will need it as `<profile-id>` in the requests below.
Returns 422 if the uploaded file is not PDF or Markdown.
---
#### `GET /profiles/{profile_id}` — Retrieve a profile 🔒
Requires authentication. Returns 404 if not found or not owned by the
authenticated user.
```bash
curl -s http://localhost:8000/profiles/<profile-id> \
  -H "Authorization: Bearer <your-token>"
```
**Response (200 OK):**
```json
{
  "id": "4af2e07d-857c-4754-b246-735d26abcc33",
  "user_id": "c6a8a47e-8b2f-48e8-8b77-eb9c6a3931df",
  "github_username": "your-github-handle",
  "portfolio_url": "https://yoursite.io",
  "created_at": "2026-07-28T03:54:20.780690Z",
  "resume_filename": null
}
```
---
#### `PUT /profiles/{profile_id}` — Update a profile 🔒
Requires authentication. Accepts a JSON body with any combination of
`github_username` and `portfolio_url`. Returns 404 if not found or not owned
by the authenticated user.
```bash
curl -s -X PUT http://localhost:8000/profiles/<profile-id> \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"github_username": "new-handle"}'
```
**Response (200 OK):**
```json
{
  "id": "4af2e07d-857c-4754-b246-735d26abcc33",
  "user_id": "c6a8a47e-8b2f-48e8-8b77-eb9c6a3931df",
  "github_username": "new-handle",
  "portfolio_url": "https://yoursite.io",
  "created_at": "2026-07-28T03:54:20.780690Z",
  "resume_filename": null
}
```
---
#### `DELETE /profiles/{profile_id}` — Delete a profile 🔒
Requires authentication. Cascade-deletes associated reviews and ingested
sources. Returns 404 if not found or not owned by the authenticated user.
```bash
curl -s -X DELETE http://localhost:8000/profiles/<profile-id> \
  -H "Authorization: Bearer <your-token>" \
  -w "\nHTTP status: %{http_code}\n"
```
**Response:** `204 No Content` — no response body. Use `-w "%{http_code}"` to
confirm the status code as shown above.
---
### Reviews
#### `POST /reviews` — Request a portfolio review 🔒
Requires authentication. Triggers the ingestion pipeline and AI agent
asynchronously. Returns immediately with `status: "pending"` — poll
`GET /reviews/{review_id}` until the status changes to `"complete"` or
`"failed"`.
```bash
curl -s -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "<profile-id>"}'
```
**Response (200 OK):**
```json
{
  "id": "712081c3-fdde-48ad-8524-28a6b9314275",
  "profile_id": "4af2e07d-857c-4754-b246-735d26abcc33",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-07-28T03:55:09.392833Z",
  "updated_at": "2026-07-28T03:55:09.392835Z"
}
```
Save the `id` — you will need it as `<review-id>` below.
---
#### `GET /reviews/{review_id}` — Retrieve a completed review 🔒
Requires authentication. Returns 404 if not found or not owned by the
authenticated user.
```bash
curl -s http://localhost:8000/reviews/<review-id> \
  -H "Authorization: Bearer <your-token>"
```
**Response (200 OK — status: complete):**
```json
{
  "id": "712081c3-fdde-48ad-8524-28a6b9314275",
  "profile_id": "4af2e07d-857c-4754-b246-735d26abcc33",
  "status": "complete",
  "sections": [
    {
      "section_name": "Technical Skills",
      "content": "Detailed feedback on technical skills based on portfolio analysis",
      "confidence": 0.85,
      "suggestions": [
        "Add more detail on AI/ML experience",
        "Include specific technologies and frameworks"
      ]
    }
  ],
  "overall_score": 0.81,
  "error_message": null,
  "created_at": "2026-07-28T03:55:09.392833Z",
  "updated_at": "2026-07-28T03:55:09.402839Z"
}
```
---
#### `GET /reviews` — List reviews for the current user (paginated) 🔒
Requires authentication. Supports `page` and `page_size` query parameters
(defaults: `page=1`, `page_size=20`, max `page_size=100`).
```bash
curl -s "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer <your-token>"
```
**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "712081c3-fdde-48ad-8524-28a6b9314275",
      "profile_id": "4af2e07d-857c-4754-b246-735d26abcc33",
      "status": "complete",
      "sections": ["..."],
      "overall_score": 0.81,
      "error_message": null,
      "created_at": "2026-07-28T03:55:09.392833Z",
      "updated_at": "2026-07-28T03:55:09.402839Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```
---
#### `GET /reviews/{review_id}/status` — Get review status and progress 🔒
Requires authentication. Useful for polling while a review is processing.
Returns 404 if not found or not owned by the authenticated user.
```bash
curl -s http://localhost:8000/reviews/<review-id>/status \
  -H "Authorization: Bearer <your-token>"
```
**Response (200 OK):**
```json
{
  "review_id": "712081c3-fdde-48ad-8524-28a6b9314275",
  "status": "complete",
  "progress_pct": 0
}
```
