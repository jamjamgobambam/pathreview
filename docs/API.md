# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

**Example:**

```bash
curl http://localhost:8000/health
```

---

### Authentication

#### Register

`POST /auth/register` — Create a new account and return a JWT access token.

**Example:**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

#### Login

`POST /auth/login` — Obtain a JWT access token.

> **Note:** This endpoint uses OAuth2 form data. Although you log in with your email address, the form field is named `username`.

**Example:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword"
```

Save the returned `access_token` and replace `<token>` in the authenticated examples below.

---

### Profiles

#### Create Profile

`POST /profiles` — Create a profile with an optional GitHub username, portfolio URL, and resume upload.

**Example:**

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <token>" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://example.com" \
  -F "resume_file=@resume.pdf"
```

> **Note:** `resume_file` must be a PDF or Markdown file. All fields are optional.

#### Retrieve Profile

`GET /profiles/{profile_id}` — Retrieve a profile.

**Example:**

```bash
curl http://localhost:8000/profiles/<profile_id> \
  -H "Authorization: Bearer <token>"
```

#### Delete Profile

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

**Example:**

```bash
curl -X DELETE http://localhost:8000/profiles/<profile_id> \
  -H "Authorization: Bearer <token>"
```

---

### Reviews

#### Create Review

`POST /reviews` — Request a new portfolio review for a profile.

**Example:**

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "<profile_id>"
  }'
```

#### Retrieve Review

`GET /reviews/{review_id}` — Retrieve a completed review.

**Example:**

```bash
curl http://localhost:8000/reviews/<review_id> \
  -H "Authorization: Bearer <token>"
```

#### List Reviews

`GET /reviews` — List reviews for the authenticated user (paginated).

**Example:**

```bash
curl "http://localhost:8000/reviews?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"
```

## Interactive Docs

When the API is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
