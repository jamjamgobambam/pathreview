# Plan: Add example `curl` commands to API docs (#117)

## Problem

`docs/API.md` lists each endpoint’s purpose but has no example invocations.
Developers bringing PathReview up for the first time cannot copy-paste a
quick smoke test from the docs. Reproduced locally: `GET /health` responds,
but the doc page still shows only one-line descriptions (see `JOURNAL.md`
Week 8).

## Goal

Add accurate, copy-pasteable `curl` examples under every endpoint currently
documented in `docs/API.md`, so a first-time setup can verify the API without
opening Swagger first.

## Success criteria

- [ ] Each documented endpoint in `docs/API.md` has at least one example `curl`
- [ ] Examples match real request shapes (JSON vs form vs multipart) from the route handlers
- [ ] Auth examples show how to obtain and reuse a Bearer token
- [ ] Placeholders (`YOUR_TOKEN`, IDs, file paths) are clearly labeled
- [ ] Examples were run against a local server where practical; known `/health` probe quirks noted briefly if needed

## Files

| File | Role |
|---|---|
| `docs/API.md` | **Only file to edit** — add examples under existing sections |
| `api/routes/auth.py` | Reference — register is JSON; login is OAuth2 form (`username`/`password`) |
| `api/routes/profiles.py` | Reference — create profile is `multipart/form-data` |
| `api/routes/reviews.py` | Reference — create review is JSON `{ "profile_id": "..." }` |
| `api/routes/health.py` | Reference — `GET /health` (may return 503 while still returning JSON) |
| `api/schemas/*.py` | Reference — field names and required bodies |

**Out of scope:** Changing route code, fixing health-check bugs (#154/#155),
frontend, new endpoints, or expanding API behavior.

## Approach (steps)

### 1. Align docs with real request formats

Confirm from handlers (not guess):

- `POST /auth/register` — JSON body: `email`, `password`
- `POST /auth/login` — form body: `username` (email), `password` (`OAuth2PasswordRequestForm`)
- `POST /profiles` — multipart form: optional `github_username`, `portfolio_url`, `resume_file`; requires `Authorization: Bearer`
- `GET`/`DELETE /profiles/{profile_id}` — Bearer auth
- `POST /reviews` — JSON `{ "profile_id": "<uuid>" }` + Bearer
- `GET /reviews`, `GET /reviews/{review_id}` — Bearer; list supports `page` / `page_size`

### 2. Draft examples in `docs/API.md`

For each section (Health → Auth → Profiles → Reviews):

1. Keep the existing one-line description.
2. Add a fenced `bash` block with a working `curl`.
3. For auth-protected routes, show `-H "Authorization: Bearer YOUR_TOKEN"`.
4. After login, show assigning the token to a shell variable (e.g. `TOKEN=...`) so later examples stay short.

Suggested order in the doc (matches a first-time smoke path):

1. Health  
2. Register (optional) / Login with seed user  
3. Create profile (multipart, optional sample `.md` resume)  
4. Create review / get review / list reviews  
5. Get / delete profile  

Use seed credentials from setup docs where helpful:

- `user1@example.com` / `password1`

### 3. Verify each example locally

With `make run` (and Docker services up):

1. Run health curl — document that a JSON body may arrive with HTTP 503 due to known probe bugs; still valid as a reachability check.
2. Login with seed user; capture `access_token`.
3. Run one profile and one review example if DB is seeded; otherwise keep placeholders and note prerequisites (`make setup` / seed).

### 4. Polish

- Keep examples short; prefer `curl -s` and note pretty-printing is optional (`| jq`).
- Do not duplicate Swagger — point to `/docs` remains fine at the bottom.
- Match naming and base URL already in the file: `http://localhost:8000`.

## Example sketches (to flesh out in the doc)

**Health**

```bash
curl -s http://localhost:8000/health
```

**Login (form-encoded — not JSON)**

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=password1"
```

**Register (JSON)**

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@example.com","password":"password123"}'
```

**Create profile (multipart + Bearer)**

```bash
curl -s -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "github_username=octocat" \
  -F "portfolio_url=https://example.com" \
  -F "resume_file=@./resume.md;type=text/markdown"
```

**Create review**

```bash
curl -s -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id":"YOUR_PROFILE_UUID"}'
```

## Risks & unknowns

| Risk | Mitigation |
|---|---|
| Login mistaken as JSON (common) | Document form fields explicitly; verify against `auth.py` |
| `/health` returns 503 | Note in Health section that JSON + 503 can still mean “API up”; do not “fix” health in this PR |
| Profile create needs a real file | Provide a minimal markdown path example; mark optional fields |
| Reviews need a real `profile_id` | Use placeholder + “from create-profile response” |
| Seed users missing if DB not seeded | Mention `make setup` / `make seed` as prerequisite |

## Test plan (for the docs PR)

1. Fresh reader path: start at Health example → Login → authenticated call.
2. Compare each curl’s method/path/headers/body to FastAPI Swagger at `/docs`.
3. Spot-check that no example invents fields not present in schemas/routes.
4. `make check` / unit tests unchanged (docs-only change).

## Estimated effort

2–3 hours (matches issue label): ~1h draft against routes, ~1h verify curls, ~30–60m polish + PR.
