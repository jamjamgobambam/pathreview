## Solution plan

**Issue:** API reference doc is missing the `POST /profiles` request body schema — https://github.com/ascherj/pathreview/issues/89

### Understand
`docs/API.md` documents response shapes for every endpoint but omits request bodies for `POST /profiles` and `POST /reviews`. The actual behavior, visible via FastAPI's auto-generated schema at `/docs`, is that `POST /profiles` takes `multipart/form-data` (`github_username`, `portfolio_url`, optional `resume_file`), while `POST /reviews` takes plain JSON (`profile_id` only). Neither request shape was documented, so a new API consumer had no way to know how to call these endpoints without reading the source.

### Map
- `docs/API.md` — the file being fixed
- `api/routes/profiles.py` — defines the `POST /profiles` endpoint and its `Form`/`File` parameters
- `api/schemas/profile.py` — `ProfileCreate` pydantic model (field constraints)
- `api/routes/reviews.py` — defines the `POST /reviews` endpoint
- `api/schemas/review.py` — `ReviewCreate` pydantic model

### Plan
1. Trace the `POST /profiles` route and schema to confirm exact fields, types, and constraints.
2. Trace the `POST /reviews` route and schema the same way.
3. Add field tables and example requests to `docs/API.md` for both endpoints.
4. Call out the multipart vs JSON distinction explicitly, since it's easy to miss.
5. Verify examples against the running Swagger UI at `/docs`.

### Inputs & outputs
Input: the existing route/schema source files. Output: an updated `docs/API.md` with accurate, example-backed request schemas for both endpoints.

### Risks & unknowns
- Field constraints (max lengths) could drift from the doc later if the schema changes, since nothing ties them together automatically.
- Resume file type validation happens at runtime (`file_mime` check) rather than in the pydantic schema, so it's easy to under-document allowed types if only reading `ProfileCreate`.

### Edge cases
- No resume file provided (`resume_file` is optional).
- Unsupported file type upload (should surface as `422`, per the route code).
- Missing `profile_id` on `POST /reviews` (schema validation, not custom code).
