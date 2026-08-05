# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl http://localhost:8000/health
```

HTTP 200 - PostgreSQL, Redis, and Vector DB dependencies are all healthy

HTTP 503 - If any dependency is down

### Authentication

`POST /auth/register` — Create a new account.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "johndoe@gmail.com", "password": "password10"}'
```
Getting Your Bearer Token:
Once you register an account, you will get an Bearer Access Token, it will appear in your CLI as an output. Save it because you will need it for the endpoints below. 

HTTP 200 - Successfully registered.

HTTP 400 - Email already exists.

HTTP 500 - Registration error

`POST /auth/login` — Obtain a JWT access token.

```bash
curl -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=johndoe@gmail.com&password=password10"
```

HTTP 200 - Successful login 

HTTP 401 - Invalid Credentials 

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -F "github_username=johndoe" \
  -F "portfolio_url=https://johndoe.dev" \
  -F "resume_file=@resume.txt;type=text/plain"
```

HTTP 200 - Success

HTTP 422 - file is not PDF, markdown or text

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl -X POST http://localhost:8000/profiles/{profile_id} \
     -H "Authorization: Bearer <YOUR_TOKEN>" 
```

HTTP 200 - Success

HTTP 404 - Profile Not Found

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -X DELETE http://localhost:8000/profiles/{profile_id} \
     -H "Authorization: Bearer <YOUR_TOKEN>" 
```  

HTTP 200 - Success

HTTP 204 - Success But No Content, empty JSON 

HTTP 404 - Profile Not Found

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "{profile_id}"}'
```

HTTP 200 - Success

HTTP 404 - Review Not Found

HTTP 505 - Internal Server Error 

`GET /reviews/{review_id}` — Retrieve a completed review.

```bash
curl http://localhost:8000/reviews/{review_id} \ 
     -H "Authorization: Bearer <YOUR_TOKEN>" 
```

HTTP 200 - Success

HTTP 404 - Review Not Found

`GET /reviews` — List reviews for the authenticated user (paginated).

```bash
curl "http://localhost:8000/reviews?page=1&page_size=20" \
     -H "Authorization: Bearer <YOUR_TOKEN>"
```

HTTP 200 - Success

HTTP 500 - Internal Server Error

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
