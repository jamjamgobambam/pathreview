# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health

`GET /health` — Returns service status and dependency health.

```bash
curl http://localhost:8000/health
```

### Authentication

`POST /auth/register` — Create a new account.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "password": "password1"}'
```

`POST /auth/login` — Obtain a JWT access token.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "password": "password1"}'
```

The response includes an `access_token`. Export it for use in the examples below:

```bash
export TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "password": "password1"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_username": "octocat", "resume_text": "Software engineer with 5 years of experience..."}'
```

`GET /profiles/{profile_id}` — Retrieve a profile.

```bash
curl -X GET http://localhost:8000/profiles/1 \
  -H "Authorization: Bearer $TOKEN"
```

`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

```bash
curl -X DELETE http://localhost:8000/profiles/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.

```bash
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": 1}'
```

`GET /reviews/{review_id}` — Retrieve a completed review.

```bash
curl -X GET http://localhost:8000/reviews/1 \
  -H "Authorization: Bearer $TOKEN"
```

`GET /reviews` — List reviews for the authenticated user (paginated).

```bash
curl -X GET "http://localhost:8000/reviews?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive Docs

When the API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Try It Yourself

After running `make setup` (see [SETUP.md](./SETUP.md)), the database is seeded with three test
accounts (`user1@example.com` / `password1`, and similarly for `user2`/`user3`). Use the login
example above to get a token, then walk through the profile and review examples in order —
create a profile, request a review, then fetch it.
