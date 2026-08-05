## Solution plan

**Issue:** #117 — API docs don't include example curl commands (https://github.com/ascherj/pathreview/issues/117)

### Understand
docs/API.md lists every endpoint as a one-line method + path with a short description, but it never shows an actual request. There's no root cause in code here since this isn't a bug, it's a documentation gap. The expected behavior is that a developer setting up the project for the first time should be able to copy a curl command straight out of docs/API.md, paste it into their terminal, and get back a real response without having to open route source files first.

I confirmed this gap is real by trying to call a couple of the endpoints myself using only what's in docs/API.md. For `POST /auth/login` I assumed a JSON body at first (since that's what `POST /auth/register` looks like it would take), but the route actually expects an OAuth2 form body with `username`/`password` fields, not JSON. I only found that by reading `api/routes/auth.py`. For `POST /profiles` I assumed JSON too, but it's multipart form data with a `resume_file` upload, which I only found in `api/routes/profiles.py`. So the actual problem isn't just "no examples," it's that some of these endpoints have request shapes that aren't guessable from the docs at all, and getting them wrong wastes a new contributor's time.

### Map
Files I expect to touch:
- `docs/API.md` — this is the only file I need to change. I'll add a curl example under each endpoint, plus a short "Example response" where it's not obvious.
- `api/routes/health.py` — reference only, to confirm the exact response shape for `GET /health` (`status`, `dependencies`, `safety_events_last_hour`, `timestamp`).
- `api/routes/auth.py` — reference only, to confirm `UserCreate`/`Token` schemas and that login is form-encoded, not JSON.
- `api/schemas/user.py` — reference only, for exact field names/types (`email`, `password`, `access_token`, `token_type`).
- `api/routes/profiles.py` — reference only, to confirm the multipart form fields for create, and the path param for get/delete.
- `api/schemas/profile.py` — reference only, for `ProfileCreate`/`ProfileResponse` field names.
- `api/routes/reviews.py` — reference only, to confirm `ReviewCreate` body, path params, and the `page`/`page_size` query params on list.
- `api/schemas/review.py` — reference only, for `ReviewResponse`/`ReviewListResponse`/`FeedbackSection` field names.
- `docs/SETUP.md` — reference only, for the seeded test credentials, so my curl examples log in with an account that actually exists after `make setup`.

I'm not touching any route or schema files. This is docs-only.

### Plan
1. Run `make setup` then `make run`, confirm the app is up, and log in with one of the seeded test accounts from `docs/SETUP.md` to get a real access token I can reuse in the other examples.
2. For each endpoint in docs/API.md, write a curl command that matches the actual request shape from the route/schema files above (correct content type, correct field names, path/query params filled in with realistic values), and run it against my local instance to confirm it actually works.
3. Add a short example JSON response under each endpoint where the shape isn't obvious from the description alone (register/login token response, profile response, review response with `sections`/`overall_score`, paginated review list).
4. Add a one-line note near the top of docs/API.md explaining that most endpoints require the `Authorization: Bearer <token>` header from the login response, so I don't have to repeat that explanation under every single endpoint.
5. Re-read the whole doc top to bottom pretending I'm a first-time contributor with nothing but this file and `make run`, and check every example is copy-pasteable as-is.

### Inputs & outputs
**What I'm changing:** docs/API.md only, no code.

**Input to my change:** the current doc (method + path + one-line description per endpoint), plus the real request/response shapes from the route and schema files listed in Map.

**Output:** the same doc, with a runnable curl example and (where useful) an example response under each endpoint, so a new contributor can verify the API works end to end (register → login → create profile → request review) using nothing but this file.

**Example I'll verify against real output:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=user1@example.com&password=password1"
```
Expected: 200 with `{"access_token": "...", "token_type": "bearer"}`. I'll run this against my local instance before I put it in the doc, not just guess the shape.

### Risks & unknowns
1. **I'm not 100% sure the seeded test accounts from docs/SETUP.md are active by default after a fresh `make setup`.** If login fails with one of them, I'll check the seed script instead of guessing and adjust the example account.
2. **The `resume_file` upload example needs an actual small PDF or markdown file to attach with curl's `-F`.** There's no fixture file in `tests/` I can point to, so I'll need to create a tiny throwaway sample resume for the example, or use a plain `.md` file inline since the multipart field accepts markdown too.
3. **Scope creep risk:** while reading the route files I found two endpoints that exist in code but aren't listed in docs/API.md at all: `GET /reviews/{review_id}/status` (`reviews.py`) and `PUT /profiles/{profile_id}` (`profiles.py`). It would be tempting to add both to the doc since I already found them, but issue #117 is scoped to adding curl examples to the endpoints already listed, not auditing the doc for missing endpoints. I'll flag both as a follow-up note instead of adding them in this PR.

### Edge cases
- `POST /auth/register` with an email that already exists: doc should show this returns 400, not just the happy path.
- `GET /profiles/{profile_id}` / `DELETE /profiles/{profile_id}` for a profile that isn't yours or doesn't exist: returns 404, worth a one-line note so people don't think the example UUID is special.
- `POST /profiles` with no resume file and no github_username (both optional): I should check what happens if someone posts an empty profile, since the doc implies at least one is expected.
- `GET /reviews` with no reviews yet for a fresh account: should show an empty `items` list with `total: 0`, not just a populated example, so people don't assume something's broken.
