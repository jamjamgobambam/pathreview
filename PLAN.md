## Solution plan

**Issue:** [API reference doc is missing the POST /profiles request body schema](https://github.com/ascherj/pathreview/issues/89)

### Understand

The root cause is that `docs/API.md` lists `POST /profiles` and `POST /reviews` by name only — no request body schema, field descriptions, types, or example values are provided. A developer reading the docs cannot construct a valid request without inspecting the source code directly.

Expected behavior: each POST endpoint entry in `docs/API.md` should include the content type, a table or list of accepted fields (name, type, required/optional, description, constraints), and a concrete example request.

Actual behavior: both POST entries are a single line with no additional detail.

### Map

Files involved in the fix:

- `docs/API.md` — the only file that needs to change; this is where the request body schemas will be added
- `api/routes/profiles.py` — source of truth for `POST /profiles`; the endpoint accepts `multipart/form-data` with `github_username`, `portfolio_url`, and `resume_file`
- `api/schemas/profile.py` — defines `ProfileCreate` (github_username, portfolio_url) and `ProfileResponse`
- `api/routes/reviews.py` — source of truth for `POST /reviews`; the endpoint accepts a JSON body
- `api/schemas/review.py` — defines `ReviewCreate` (profile_id: UUID, required)

No other files need to be modified.

### Plan

1. **Document `POST /profiles` request body** — expand the `POST /profiles` line in `docs/API.md` to note that the content type is `multipart/form-data`, list each field (`github_username`, `portfolio_url`, `resume_file`) with its type, required/optional status, constraints (max lengths, accepted MIME types), and a curl example.

2. **Document `POST /reviews` request body** — expand the `POST /reviews` line to note that the content type is `application/json`, list the `profile_id` field (UUID, required), and add a JSON example body.

3. **Add response schema summaries** — add brief notes on what each endpoint returns (status code, response shape) so the docs are consistent across both endpoints.

4. **Remove the reproduction TODO comments** — delete the `<!-- TODO #89: ... -->` markers added in the reproduction commit once the full schema documentation is in place.

5. **Verify accuracy** — cross-check every field name, type, and constraint in the documentation against the Pydantic schemas and route definitions to confirm nothing is misrepresented.

### Inputs & outputs

**Input:** the current `docs/API.md`, `api/schemas/profile.py`, `api/schemas/review.py`, `api/routes/profiles.py`, and `api/routes/reviews.py`

**Output:** an updated `docs/API.md` where `POST /profiles` and `POST /reviews` each include: content type, field table with name/type/required/description/constraints, and an example request body

### Risks & unknowns

- `POST /profiles` uses `multipart/form-data` (not JSON) because it accepts a file upload via `UploadFile`. This is different from a standard JSON body and may require a curl example with `-F` flags rather than `-d '{...}'`. The documentation format needs to clearly communicate this distinction so developers know to send the right content type.
- The `resume_file` field accepts `application/pdf`, `text/markdown`, and `text/plain`. Documenting all three accepted MIME types clearly is important; missing one could mislead developers.
- The `ProfileCreate` Pydantic schema has `github_username` and `portfolio_url`, but the route reads these as `Form(...)` parameters rather than from the model directly. The documentation should reflect the actual wire format (form fields), not just the schema class.

### Edge cases

- A request to `POST /profiles` with no fields at all is valid — all fields are optional. The docs should make clear that no fields are strictly required.
- A request to `POST /profiles` with an unsupported file type returns HTTP 422. This error case should be noted alongside the `resume_file` field description.
- A request to `POST /reviews` referencing a `profile_id` that does not belong to the authenticated user will fail. This is an authorization edge case worth noting in the docs.
- The `profile_id` in `POST /reviews` must be a valid UUID; a malformed string will produce a 422 validation error. The example should use a realistic UUID value to set correct expectations.
