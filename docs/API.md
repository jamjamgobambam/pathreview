# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.
  Check the health of PostgreSQL, Redis, and the Vector Database. Returns **200** if all dependencies are healthy, or **503** if one or more dependencies are unavailable.

**Authentication:** Not required

**Example**

```bash
curl -X GET http://localhost:8000/health \
  -H "accept: application/json"
```

**Successful Response (200)**

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "2026-07-29T02:11:37.873649"
}
```

**Service Unavailable (503)**

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
    "timestamp": "2026-07-29T02:11:37.873649"
  }
}
```

### Authentication


`POST /auth/register` — Create a new account.

**Example**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "stringst"
  }'
```

**Successful Response (200)**

```json
{
  "access_token": "<JWT_ACCESS_TOKEN>",
  "token_type": "bearer"
}
```

**Validation Error (422)**

Returned when the request body is missing required fields or contains invalid values.


`POST /auth/login` — Obtain a JWT access token.

Login with email and password. Returns a JWT access token if the credentials are valid.

**Example**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=&username=user@example.com&password=stringst&scope=&client_id=string&client_secret="
```

**Successful Response (200)**

```json
{
  "access_token": "<JWT_ACCESS_TOKEN>",
  "token_type": "bearer"
}
```

**Error Responses**

- **401 Unauthorized** – Invalid email or password.
- **422 Validation Error** – Missing or invalid request parameters.


### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.
 
 Create a new profile with an optional resume upload. The resume must be a PDF or Markdown file.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X POST http://localhost:8000/profiles \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -F "github_username=string" \
  -F "portfolio_url=string" \
  -F "resume_file=@resume.pdf;type=application/pdf"
```

**Successful Response (200)**

```json
{
  "id": "<PROFILE_ID>",
  "user_id": "<USER_ID>",
  "github_username": "string",
  "portfolio_url": "string",
  "created_at": "2026-07-29T01:40:55.318Z",
  "resume_filename": "resume.pdf"
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **422 Validation Error** – Invalid request or unsupported resume file type.



`GET /profiles/{profile_id}` — Retrieve a profile.
Retrieving a profile by its ID. Returns **404** if the profile does not exist or is not owned by the authenticated user.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X GET http://localhost:8000/profiles/<PROFILE_ID> \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

**Successful Response (200)**

```json
{
  "id": "<PROFILE_ID>",
  "user_id": "<USER_ID>",
  "github_username": "string",
  "portfolio_url": "string",
  "created_at": "2026-07-29T01:48:26.118Z",
  "resume_filename": "resume.pdf"
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **404 Not Found** – Profile does not exist or is not owned by the authenticated user.
- **422 Validation Error** – Invalid profile ID format.


### Update Profile

`PUT /profiles/{profile_id}` — Update an existing profile. Returns **404** if the profile does not exist or is not owned by the authenticated user.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X PUT http://localhost:8000/profiles/<PROFILE_ID> \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "github_username": "string",
    "portfolio_url": "string"
  }'
```

**Successful Response (200)**

```json
{
  "id": "<PROFILE_ID>",
  "user_id": "<USER_ID>",
  "github_username": "string",
  "portfolio_url": "string",
  "created_at": "2026-07-29T01:51:04.972Z",
  "resume_filename": "resume.pdf"
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **404 Not Found** – Profile does not exist or is not belong to the authenticated user.
- **422 Validation Error** – Invalid request body or invalid profile ID.


`DELETE /profiles/{profile_id}` — Delete a profile and associated data.
Delete a profile and cascade delete its associated reviews and ingested sources.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X DELETE http://localhost:8000/profiles/<PROFILE_ID> \
  -H "accept: */*" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

**Successful Response (204 No Content)**

The profile and its associated reviews and ingested sources are deleted successfully. No response body is returned.

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **404 Not Found** – Profile does not exist or is not owned by the authenticated user.
- **422 Validation Error** – Invalid profile ID format.


### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
Creating a new review for a profile. The review is created immediately with a status of `pending`, while the ingestion pipeline and review agents run asynchronously.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X POST http://localhost:8000/reviews \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "<PROFILE_ID>"
  }'
```

**Successful Response (200)**

```json
{
  "id": "<REVIEW_ID>",
  "profile_id": "<PROFILE_ID>",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-07-29T02:01:21.583Z",
  "updated_at": "2026-07-29T02:01:21.583Z"
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **404 Not Found** – The specified profile does not exist or is not owned by the authenticated user.
- **422 Validation Error** – Invalid request body or invalid profile ID.


`GET /reviews/{review_id}` — Retrieve a completed review.
Retrieve a review by its ID. Returns **404** if the review does not exist or is not owned by the authenticated user.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X GET http://localhost:8000/reviews/<REVIEW_ID> \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

**Successful Response (200)**

```json
{
  "id": "<REVIEW_ID>",
  "profile_id": "<PROFILE_ID>",
  "status": "completed",
  "sections": [
    {
      "section_name": "Experience",
      "content": "...",
      "confidence": 0.95,
      "suggestions": [
        "Add measurable achievements."
      ]
    }
  ],
  "overall_score": 85,
  "error_message": null,
  "created_at": "2026-07-29T02:07:54.351Z",
  "updated_at": "2026-07-29T02:07:54.351Z"
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **404 Not Found** – Review does not exist or is not owned by the authenticated user.
- **422 Validation Error** – Invalid review ID format.

 
`GET /reviews` — List reviews for the authenticated user (paginated).

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X GET "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

**Successful Response (200)**

```json
{
  "items": [
    {
      "id": "<REVIEW_ID>",
      "profile_id": "<PROFILE_ID>",
      "status": "completed",
      "sections": [
        {
          "section_name": "Experience",
          "content": "...",
          "confidence": 0.95,
          "suggestions": [
            "Add measurable achievements."
          ]
        }
      ],
      "overall_score": 85,
      "error_message": null,
      "created_at": "2026-07-29T02:04:34.360Z",
      "updated_at": "2026-07-29T02:04:34.360Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **422 Validation Error** – Invalid pagination parameters.


### Get Review Status

`GET /reviews/{review_id}/status` — Retrieve the current status and progress of a review. Returns the review ID, current status, and completion percentage.

**Authentication:** Required (`Bearer` token)

**Example**

```bash
curl -X GET http://localhost:8000/reviews/<REVIEW_ID>/status \
  -H "accept: application/json" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

**Successful Response (200)**

```json
{
  "review_id": "<REVIEW_ID>",
  "status": "pending",
  "progress_pct": 35
}
```

**Error Responses**

- **401 Unauthorized** – Missing or invalid Bearer token.
- **404 Not Found** – Review does not exist or is not owned by the authenticated user.
- **422 Validation Error** – Invalid review ID format.


### Root

`GET /` — Verify that the PathReview API is running and return basic service information.

**Authentication:** Not required

**Example**

```bash
curl -X GET http://localhost:8000/ \
  -H "accept: application/json"
```

**Successful Response (200)**

```json
{
  "message": "PathReview API is running",
  "version": "1.0.0"
}
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
 