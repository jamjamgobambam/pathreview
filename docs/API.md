# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

### Authentication

`POST /auth/register` — Create a new account.

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

`POST /auth/login` — Obtain a JWT access token.

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=user@example.com&password=your_password&scope=&client_id=&client_secret="
```

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

```bash
curl -X POST "http://localhost:8000/profiles" \
  -H "accept: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "github_username=your-github-username" \
  -F "portfolio_url=https://your-portfolio.example.com"
```

Optional: To upload a resume, add the following flag to the command above:

```bash
-F "resume_file=@/path/to/resume.pdf;type=application/pdf"
```

`GET /profiles/{profile_id}` — Retrieve a profile.

Profile ID was received from the previous command, save it please

```bash
curl -X GET "http://localhost:8000/profiles/{profile_id}" \
  -H "accept: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -X DELETE "http://localhost:8000/profiles/{profile_id}" \
  -H "accept: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

```bash
curl -X POST "http://localhost:8000/reviews" \
  -H "accept: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "YOUR_PROFILE_ID"
  }'
```

`GET /reviews/{review_id}` — Retrieve a completed review.

```bash
curl -X GET "http://localhost:8000/reviews/YOUR_REVIEW_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Interactive Docs

When the API is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
