## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/117

### Understand
The root cause of this issue is that the API documentation in API.md lists the available endpoints, but it does not provide practical, copy-pasteable curl examples. The expected behavior is that new contributors should be able to quickly test the API locally using clear examples; the actual behavior is that the docs are incomplete, which creates friction and slows down validation.

### Map
The files I expect to touch:

- `docs/API.md` — the primary file to update with clear, copy-pasteable curl examples for the documented endpoints.
- `JOURNAL.md` — the Week 8 entry documenting reproduction, planning, and any remaining questions or blockers.
- `PLAN.md` — this planning document, which will be updated to reflect the final approach and scope of the fix.


### Plan
1. Run the app locally (docker compose up -d, make setup, make run) and manually call each endpoint listed in docs/API.md, capturing the real request/response instead of guessing from the schema.
2. Add a curl example for GET /health (no auth needed), and for POST /auth/register and POST /auth/login. Register takes a JSON body ({"email": ..., "password": ...}); login takes application/x-www-form-urlencoded via OAuth2PasswordRequestForm, so its body is username=...&password=... (email goes in the username field), not JSON — the two examples can't share the same -H/-d shape.
3. Add examples for POST /profiles, GET /profiles/{profile_id}, and DELETE /profiles/{profile_id}. Every one needs -H "Authorization: Bearer $TOKEN". POST /profiles accepts multipart form fields (Form/File), so its example needs -F "github_username=..." -F "resume_file=@resume.pdf", not a JSON body.
4. Add examples for POST /reviews, GET /reviews/{review_id}, and GET /reviews. Use a real UUID for profile_id, show the status: "pending" response shape from ReviewResponse, and note the page/page_size query params on the list endpoint (clamped 1–100 server-side).
5. Re-run every example against the live local server to confirm it's accurate, then fix any that don't match the actual behavior.

### Inputs & outputs
- Input: the existing API documentation, the local running API, and the route definitions for the relevant endpoints. 

- Output: an updated documentation file with working curl examples that help developers test the API locally.

### Risks & unknowns
- /auth/login uses OAuth2PasswordRequestForm, so the example must use form-encoded username/password fields (email goes in username) — easy to get wrong by copying the JSON style used for /auth/register.
- Unsure whether to expand scope to document PUT /profiles/{profile_id} and GET /reviews/{review_id}/status, which exist in code but are missing from docs/API.md — may be worth flagging to a reviewer rather than deciding unilaterally.

### Edge cases
- Show error-response shapes for documented failure cases (400 "Email already registered", 401 "Invalid email or password", 404 "Profile not found", 422 invalid resume file type), not just the happy path.
- Note the pagination defaults/bounds on GET /reviews (page, page_size clamped 1–100) so the example doesn't imply unbounded page sizes.