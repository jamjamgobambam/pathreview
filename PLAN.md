## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/89

### Understand
The issue here is that there are missing response schema documentations for POST /profiles and POST /reviews in API.md

### Map
The main file involved here is API.md, however in a broader sense, api/routes/profiles.py and api/schemas/review.py are the source of truth for the documentation.

### Plan

1. Investigate profiles.py and review.py, understand structure
2. Record the response schema in API.md
3. Create an example in API.md

### Inputs & outputs
**Inputs** (source of truth to read, not assume): the FastAPI route signatures in `api/routes/profiles.py` and `api/routes/reviews.py` (which define what's actually accepted on the wire — `Form`/`File` params vs. a JSON body), and the Pydantic models in `api/schemas/profile.py` and `api/schemas/review.py` (which define field types/constraints like `max_length`). Both have to be checked, not just the schema files, since `POST /profiles` doesn't take its request body as a single Pydantic model.

**Outputs**: an updated `docs/API.md` with a request-body field table (name, type, required, description) and one worked example per endpoint, for both `POST /profiles` and `POST /reviews`.

### Risks & unknowns
- **Doc/code mismatch risk on `POST /profiles`**: `ProfileCreate` in `api/schemas/profile.py` only has 2 fields (`github_username`, `portfolio_url`). If I'd documented straight from that model, I'd have missed `resume_file` entirely and mislabeled the whole request as JSON — the route handler (`api/routes/profiles.py:24-29`) actually takes `Form`/`File` params directly and builds `ProfileCreate` internally. Confirmed by reading the handler, not just the schema.
- **Undocumented validation gap on `POST /reviews`**: `create_review` (`core/services/review_service.py:15-32`) never checks that `profile_id` exists or belongs to the caller — unlike `get_review`/`list_reviews`, which join on `Profile.user_id`. So a bad or someone-else's `profile_id` is accepted at creation time (200, `status="pending"`) and only fails later, silently, in the background task. This is arguably a bug rather than a doc gap — I'm noting it in the doc as current behavior rather than fixing it, since it's out of scope for issue #89, but it should probably be filed as a follow-up issue.
- **Unknown**: whether that missing ownership check is intentional (e.g., deferred to the background job by design) or an oversight. I'm treating it as unconfirmed and documenting only observed behavior, not intent.

### Edge cases
1. **Nullable profile fields**: `github_username`, `portfolio_url`, and `resume_file` are all optional (`api/routes/profiles.py:25-27`) — a request with none of them is valid and creates an empty-ish profile.
2. **Invalid resume file type**: uploading a `resume_file` that isn't `application/pdf`, `text/markdown`, or `text/plain` returns `422` with `"Resume must be a PDF or Markdown file"` (`api/routes/profiles.py:44-53`).
3. **Corrupted/unparseable PDF**: a `resume_file` with a valid PDF MIME type but that fails parsing returns `422` with `"Failed to parse PDF resume"` (`api/routes/profiles.py:66-71`) — a distinct failure mode from #2 that's easy to conflate in the docs.
4. **`profile_id` not owned by (or not belonging to) the caller on `POST /reviews`**: as noted above, this is accepted at creation time rather than rejected with a `404`/`403` — worth calling out explicitly so API consumers don't assume immediate validation.