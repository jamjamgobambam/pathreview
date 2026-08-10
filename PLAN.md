## Solution plan

**Issue:** #89 — API reference doc is missing the `POST /profiles` request body schema

### Understand
`docs/API.md` lists the `POST /profiles` endpoint with only a one-line description
and no request body details. Looking at the actual implementation in
`api/routes/profiles.py` (`create_profile_endpoint`), the endpoint expects
`multipart/form-data`, not JSON, because it accepts a file upload alongside
two form fields:
- `github_username` (optional, string, max 255 chars)
- `portfolio_url` (optional, string, max 500 chars)
- `resume_file` (optional, file — must be `application/pdf`, `text/markdown`,
  or `text/plain`, otherwise the endpoint returns 422)

None of this is documented, so a developer reading `docs/API.md` has no way to
know the endpoint takes form data with a file, what fields are expected, or
what happens if the resume file is the wrong type. The fix is to add the full
request body schema to the `POST /profiles` entry: field names, types,
required/optional status, the `multipart/form-data` content type, an example
request, and a note about the 422 case for invalid file types.

**Root cause:** `docs/API.md` was never updated with request body details when
`POST /profiles` was implemented — it only documents endpoint existence, not
request shape, for any endpoint in the file.


### Map
Files I expect to touch:
- `docs/API.md` — the `POST /profiles` entry under the "Profiles" section.
  This is where I'll add the full request body schema, replacing my
  reproduction comment.

Files I'm using as source of truth (not editing):
- `api/routes/profiles.py`, lines 23-30 — `create_profile_endpoint`, where
  `github_username`, `portfolio_url`, and `resume_file` are defined as
  `Form`/`File` parameters (lines 25-27). This is the real request shape.
  Lines 43-51 show the 422 error raised when `resume_file`'s content type
  isn't `application/pdf`, `text/markdown`, or `text/plain`.
- `api/schemas/profile.py` — defines `ProfileCreate`, which looks like it
  might be the request schema but isn't used directly for the request body
  (the endpoint reads the form fields individually, then builds a
  `ProfileCreate` internally at line ~76). Worth noting so I don't document
  this model as if it were the literal request body.


### Plan
1. Re-read `api/routes/profiles.py` lines 23-30 and 43-51 one more time to
   lock in exact field names, types, defaults, and the file-type validation
   list before writing anything.
2. Draft the `POST /profiles` doc section in `docs/API.md`: content type
   (`multipart/form-data`), each field with its type and optional/required
   status, matching what's in the route.
3. Add an example request showing all three fields, including a realistic
   filename for `resume_file`.
4. Document the 422 error case: what triggers it (invalid file MIME type)
   and what the response looks like.
5. Remove my reproduction comment and proofread the final section against
   the route one more time to check for drift.

### Inputs & outputs
**File I'm changing:** `docs/API.md`

**Input to my change:** the actual behavior of `create_profile_endpoint` in
`api/routes/profiles.py` — I'm not changing any code, just documenting what
already exists.

**Output:** an updated `POST /profiles` section in `docs/API.md` containing:
- Content type: `multipart/form-data`
- Field list: `github_username` (optional, string, max 255), `portfolio_url`
  (optional, string, max 500), `resume_file` (optional, file — PDF, Markdown,
  or plain text)
- An example request
- A note on the 422 response when `resume_file`'s type is invalid

### Risks & unknowns
1. **Scoping to /profiles only.** Issue #89 mentions both `POST /profiles`
   and `POST /reviews`, but my JOURNAL.md and this plan only cover
   `/profiles`, matching the issue title. Flagging this so it reads as a
   deliberate choice, not a missed requirement.
2. **Doc formatting consistency.** `docs/API.md` currently has a very sparse
   style (one-line descriptions, no schemas anywhere). I'm not sure how
   detailed to make the new section without it looking out of place next to
   the other entries — I'll check if there's a formatting convention in
   `docs/CONTRIBUTING.md` before finalizing.
3. **Example values.** I need to pick a realistic example for `resume_file`
   (filename, maybe a fake GitHub username) — nothing in the codebase gives
   me a canonical example to copy, so I'm making a reasonable one up.

### Edge cases
- All fields optional means a technically valid request could send an empty
  body — worth noting in the docs so readers don't assume something is
  required when it isn't.
- `resume_file` omitted entirely: profile still gets created, just without
  resume text/filename.
- `resume_file` present but wrong MIME type (not PDF/Markdown/plain text):
  422 response, documented separately from the happy path.