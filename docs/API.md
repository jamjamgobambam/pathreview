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

Every curl example below was run against a local instance (`make setup` + `make run`) and the responses shown are the real output. To follow along yourself, log in with one of the seeded test accounts from [SETUP.md](SETUP.md) (e.g. `user1@example.com` / `password1`) and reuse the `access_token` from that response as the `Authorization: Bearer <token>` header on every request below that needs one.

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl http://localhost:8000/health
```

Example response (a fresh local instance currently reports `postgres` and `redis` as unhealthy due to a pre-existing bug in the health check code):

```json
{
  "detail": {
    "status": "unhealthy",
    "dependencies": {
      "postgres": "unhealthy",
      "redis": "unhealthy",
      "vector_db": "healthy"
    },
    "safety_events_last_hour": 0,
    "timestamp": "2026-07-29T00:00:33.675937"
  }
}
```

### Authentication

`POST /auth/register` — Create a new account.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword123"}'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

If the email is already registered, this returns `400` with `{"detail": "Email already registered"}`.

`POST /auth/login` — Obtain a JWT access token.

This is an OAuth2 form login, not JSON, the body is form-encoded with `username` and `password` fields (`username` is your email).

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=you@example.com&password=yourpassword123"
```

Response (same shape as register):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save the token to a variable so you can reuse it in the examples below:

```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

This is a multipart form, not JSON, `github_username` and `portfolio_url` are optional form fields, and `resume_file` is an optional file upload (PDF, Markdown, or plain text).

Create a small resume file to upload (or point `-F` at any PDF/Markdown file you already have):

```bash
echo "# Jane Doe

Software engineer with 3 years of experience." > resume.md
```

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -F "github_username=octocat" \
  -F "resume_file=@resume.md;type=text/markdown"
```

curl doesn't reliably guess a file's MIME type on its own, so you need the explicit `;type=...` — without it, the server may reject the upload with `422` even though the file itself is fine. Use whichever type matches your actual resume file:

- Markdown (`.md`): `-F "resume_file=@resume.md;type=text/markdown"`
- Plain text (`.txt`): `-F "resume_file=@resume.txt;type=text/plain"`
- PDF (`.pdf`): `-F "resume_file=@resume.pdf;type=application/pdf"`

Response:

```json
{
  "id": "af9d9089-6fd3-456b-85b6-edf5f0f86fa6",
  "user_id": "ab5fcbce-7b64-4e53-8016-7b547d09457f",
  "github_username": "octocat",
  "portfolio_url": null,
  "created_at": "2026-07-29T04:02:18.300406Z",
  "resume_filename": "resume.md"
}
```

If `resume_file` is present but isn't PDF, Markdown, or plain text, this returns `422` with `{"detail": "Resume must be a PDF or Markdown file"}` (the error message itself doesn't mention plain text, even though it's accepted too). Both `github_username` and `resume_file` are actually optional, posting neither still succeeds with `200` and a profile that has `github_username`, `portfolio_url`, and `resume_filename` all `null`.

`GET /profiles/{profile_id}` — Retrieve a profile.

Swap in the `id` from the create-profile response above (`af9d9089-...` below is only the example from when this doc was written):

```bash
curl http://localhost:8000/profiles/af9d9089-6fd3-456b-85b6-edf5f0f86fa6 \
  -H "Authorization: Bearer $TOKEN"
```

Response (same shape as the create response, repeated here for convenience):

```json
{
  "id": "af9d9089-6fd3-456b-85b6-edf5f0f86fa6",
  "user_id": "ab5fcbce-7b64-4e53-8016-7b547d09457f",
  "github_username": "octocat",
  "portfolio_url": null,
  "created_at": "2026-07-29T04:02:18.300406Z",
  "resume_filename": "resume.md"
}
```

If the profile doesn't exist or isn't yours, this returns `404` with `{"detail": "Profile not found"}`, the same response either way, so a mistyped ID looks identical to someone else's profile.

`DELETE /profiles/{profile_id}` — Delete a profile and associated data. This is shown at the end of this doc, since deleting a profile also cascades to its reviews, run it last, after you've tried the review examples below, not now.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

Swap in the `id` from the create-profile response above (`af9d9089-...` below is only the example from when this doc was written):

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "af9d9089-6fd3-456b-85b6-edf5f0f86fa6"}'
```

Review generation runs in the background, so the response you get right away is `pending` with empty results:

```json
{
  "id": "4e8bd8dd-1588-420a-95df-8d0c532bd933",
  "profile_id": "af9d9089-6fd3-456b-85b6-edf5f0f86fa6",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-07-29T04:02:32.102959Z",
  "updated_at": "2026-07-29T04:02:32.102961Z"
}
```

Poll `GET /reviews/{review_id}` until `status` is `complete` (or `failed`) to get the actual feedback.

`GET /reviews/{review_id}` — Retrieve a completed review.

Swap in the `id` from the create-review response above (`4e8bd8dd-...` below is only the example from when this doc was written):

```bash
curl http://localhost:8000/reviews/4e8bd8dd-1588-420a-95df-8d0c532bd933 \
  -H "Authorization: Bearer $TOKEN"
```

Once the review finishes, the response looks like this (`sections` is trimmed to one entry below for brevity):

```json
{
  "id": "4e8bd8dd-1588-420a-95df-8d0c532bd933",
  "profile_id": "af9d9089-6fd3-456b-85b6-edf5f0f86fa6",
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
  "created_at": "2026-07-29T04:02:32.102959Z",
  "updated_at": "2026-07-29T04:02:32.125664Z"
}
```

`GET /reviews` — List reviews for the authenticated user (paginated).

```bash
curl "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

Response (if you've followed along above, you'll see the review you just created in `items`, `sections` is trimmed to one entry below for brevity, same as the GET /reviews/{review_id} example above):

```json
{
  "items": [
    {
      "id": "4e8bd8dd-1588-420a-95df-8d0c532bd933",
      "profile_id": "af9d9089-6fd3-456b-85b6-edf5f0f86fa6",
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
      "created_at": "2026-07-29T04:02:32.102959Z",
      "updated_at": "2026-07-29T04:02:32.125664Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

On a brand-new account with no reviews yet, `items` is an empty list with `total: 0` instead, not an error:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

### Cleanup

`DELETE /profiles/{profile_id}` — Delete a profile and associated data (reviews included).

Swap in the `id` from the create-profile response above (`af9d9089-...` below is only the example from when this doc was written):

```bash
curl -X DELETE http://localhost:8000/profiles/af9d9089-6fd3-456b-85b6-edf5f0f86fa6 \
  -H "Authorization: Bearer $TOKEN"
```

Returns `204` with an empty body on success. Deleting an already-deleted (or nonexistent) profile returns `404` with `{"detail": "Profile not found"}`.

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
