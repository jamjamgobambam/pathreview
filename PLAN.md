## Solution plan

**Issue:** #117 — API docs don't include example `curl` commands  
**Link:** https://github.com/ascherj/pathreview/issues/117

### Understand

The API documentation in `docs/API.md` describes each endpoint (method, path, brief description) but lacks example `curl` commands that developers can copy and paste to test the API. This makes it harder for developers setting up the project for the first time to verify that the API is working.

The current `docs/API.md` lists endpoints like:
- `GET /health` — health check
- `POST /auth/register` — create a new account
- `POST /auth/login` — obtain a JWT token
- `POST /profiles` — create a profile with resume and GitHub username
- `GET /profiles/{profile_id}` — retrieve a profile
- `DELETE /profiles/{profile_id}` — delete a profile
- `POST /reviews` — request a new portfolio review
- `GET /reviews/{review_id}` — retrieve a completed review
- `GET /reviews` — list reviews for the authenticated user

But none of these have working `curl` examples.

**What needs to change:** Add a `curl` example under each endpoint section in `docs/API.md`. Each example should:
1. Use the local server URL (`http://localhost:8000`)
2. Include necessary headers (e.g., `-H "Content-Type: application/json"`)
3. Include sample JSON payloads where needed
4. Show the expected response (briefly)
5. Work correctly when copied and pasted into a terminal

### Map

Files I expect to touch:
- `docs/API.md` — The main documentation file where I'll add the `curl` examples
- `api/routes/auth.py` — Authentication endpoints (to verify `/auth/register` and `/auth/login`)
- `api/routes/profiles.py` — Profile endpoints (to verify `/profiles` endpoints)
- `api/routes/reviews.py` — Review endpoints (to verify `/reviews` endpoints)
- `api/routes/health.py` — Health check endpoint (to verify `/health`)
- `api/schemas/` — Pydantic schemas (to verify request/response structures for `curl` payloads)

I'll use `http://localhost:8000/docs` (Swagger UI) to test the `curl` commands before adding them.

### Plan

1. **Read `docs/API.md`** to understand the current structure and formatting style.
2. **Visit Swagger UI at `http://localhost:8000/docs`** to see all endpoints, their request/response schemas, and test them manually.
3. **Write `curl` commands for each endpoint:**
   - `GET /health` — simple health check
   - `POST /auth/register` — include JSON payload with email/password
   - `POST /auth/login` — include form data for OAuth2 (username/password)
   - `POST /profiles` — include form data for creating a profile
   - `GET /profiles/{profile_id}` — replace `{profile_id}` with a real UUID from a created profile
   - `DELETE /profiles/{profile_id}` — include `-X DELETE` and a real UUID
   - `POST /reviews` — include JSON payload with profile_id
   - `GET /reviews/{review_id}` — replace `{review_id}` with a real UUID from a created review
   - `GET /reviews` — show pagination params (`?page=1&page_size=10`)
4. **Test each `curl` command** against the local API (`http://localhost:8000`) to ensure they work.
5. **Add the examples to `docs/API.md`** under each endpoint, following this format:

GET /health

curl -X GET http://localhost:8000/health

6. **Run `make check`** to ensure formatting and linting are clean.
7. **Verify the updated `docs/API.md`** renders correctly in the browser (it's plain Markdown).

### Inputs & outputs

**File I'm changing:** `docs/API.md`

**Existing structure:**
- Lists each endpoint with method, path, and brief description
- No examples

**New structure (added under each endpoint):**

Example

curl -X <METHOD> http://localhost:8000/<path> \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'

  
**Success criteria:**
- Every endpoint in `docs/API.md` has a working `curl` example
- Running the example returns a valid response from the local API
- The documentation remains readable and well-formatted

### Risks & unknowns

1. **Token-based authentication:** Endpoints like `GET /profiles/{profile_id}` require a JWT token. I need to:
   - First register a user: `POST /auth/register`
   - Then login: `POST /auth/login` to get a token
   - Include the token in the `Authorization` header for protected endpoints
   - The docs should show this two-step process

2. **UUIDs in paths:** `GET /profiles/{profile_id}` and `DELETE /profiles/{profile_id}` need a real UUID. I need to:
   - Create a profile first (via `POST /profiles`)
   - Capture the returned profile ID
   - Use that ID in the `curl` commands
   - The docs should note that you need to replace `{profile_id}` with your actual UUID

3. **Background tasks:** `POST /reviews` returns immediately with status "pending". The example should show the response and explain that the review processes asynchronously.

4. **OAuth2 login format:** `POST /auth/login` expects form data (not JSON). I need to use `-F` or `-d` with the correct format in `curl`.

5. **I'm not sure which sample data to use for profiles** — I'll use the seeded test accounts (`user1@example.com` / `password1`) and the test profile data that gets created.

### Edge cases

- **Empty JSON payload:** Some endpoints like `DELETE /profiles/{profile_id}` don't need a body. The example should just use `-X DELETE` with no `-d` flag.
- **Authentication error:** If the user forgets to include the token, they get a 401. The docs should mention the token requirement.
- **Invalid profile ID:** If the user uses a UUID that doesn't exist, they get a 404. The example should show the expected 404 response.
- **Missing required fields:** For `POST /auth/register` and `POST /profiles`, if required fields are missing, the API returns a 422 error. The example should show the correct payload structure.

### Verification steps
- [ ] Run `make check` — passes linting, formatting, and type checks
- [ ] Manually test each `curl` command in the docs
- [ ] Verify the updated docs are readable and well-formatted

