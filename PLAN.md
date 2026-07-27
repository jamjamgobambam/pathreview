## Solution plan

**Issue:** API reference doc is missing the POST /profiles request body schema — https://github.com/ascherj/pathreview/issues/89

### Understand

The root cause is that `docs/API.md` only lists endpoint names with a one-line
description each. It never shows the request body — the fields you send, their
types, or an example. So the info exists in the code, but not in the docs.

- Expected: a developer can read `docs/API.md` and know exactly what to send to
  `POST /profiles` and `POST /reviews`.
- Actual: they have to open the FastAPI routes and Pydantic schemas to figure it
  out. `POST /profiles` is the confusing one because it's form-data with a file
  upload, not JSON.

### Map

Files I'll touch:

- `docs/API.md` — the only file I'll edit. Add a request-body section under
  `POST /profiles` (line 18) and `POST /reviews` (line 24).

Files I'll read for the source of truth (not editing):

- `api/routes/profiles.py` — the `Form(...)`/`File(...)` params for `/profiles`.
- `api/schemas/profile.py` — `ProfileCreate` (`github_username`, `portfolio_url`).
- `api/routes/reviews.py` — the `/reviews` endpoint.
- `api/schemas/review.py` — `ReviewCreate` (`profile_id`).

### Plan

1. Add a request-body section for `POST /profiles`: note it's multipart
   form-data (not JSON), a field table (`github_username`, `portfolio_url`,
   `resume_file`), and a short `curl -F` example.
2. Add a request-body section for `POST /reviews`: note it's JSON, a field table
   with `profile_id` (UUID, required), and a short JSON example.
3. Double-check every field name, type, and required/optional against the code
   so the docs match reality.
4. Read through the whole file once to make sure the formatting and tone match
   the rest of `docs/API.md`.

### Inputs & outputs

- Input: the request-body definitions that already live in the routes and
  schemas.
- Output: an updated `docs/API.md` where both endpoints show their fields and an
  example. No code or runtime behavior changes — docs only.

### Risks & unknowns

- Low risk overall since it's docs-only, nothing runs or gets tested.
- Main risk is the docs drifting from the code (wrong field name or type), so I
  need to copy carefully from the schemas.
- Open question: `api/routes/profiles.py` also accepts plain text uploads, but
  the docstring says only PDF/Markdown. I need to decide whether the docs
  mention plain text or just match the PDF/Markdown intent.

### Edge cases

- Show which fields are optional vs. required so no one thinks they're all
  needed.
- Make it clear `/profiles` is form-data, not JSON, so people don't send the
  wrong content type.
- Note the accepted resume file types so an unsupported upload (which returns a
  422) is expected, not a surprise.
