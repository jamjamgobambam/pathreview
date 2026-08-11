## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:**  [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The API reference file `docs/API.md` documents the response shape for each
endpoint, but it never describes what data a client must send in the request
body for the two POST endpoints: `POST /profiles` and `POST /reviews`. Because of
this gap, a developer reading the docs can't tell which fields are required,
what types they should be, or what a valid example request looks like. A
successful fix adds request body schemas for both endpoints, with a description
for each field and realistic example values, so the documentation matches the
detail already provided for responses.

**Selection notes:**

- Tier fit:
This is my first contribution to a large codebase, so I'm
deliberately choosing a Tier 1 issue. It's docs-only and self-contained, which
matches where I am right now.

- Codebase readiness: I traced both endpoints to their request models:
`POST /profiles` uses ProfileCreate (`api/schemas/profile.py`), which accepts two
optional fields: github_username and portfolio_url (both strings). `POST /reviews`
uses ReviewCreate (`api/schemas/review.py`), which requires a single field,
profile_id (a UUID). I read these Pydantic classes directly, so the schemas I
document will match the fields the API actually accepts. Note: this is a
documentation-only change with no code behavior, so there is no unit test to
modify; my verification is checking the documented fields against these request
models.

- Scope and time: Estimated 2–3 hours per the issue, which fits
comfortably in the Weeks 8–9 window alongside my other commitments. I checked
the issue comments and the ledger's Claims count and I'm fine with 14 people are on it. The issue lists no blockers or dependencies.

- All boxes reasonably satisfied (with the test-file caveat noted
above), so this issue is a realistic, well-scoped Tier 1 choice for me.


**Branch name:** docs/89-add-post-request-body-schemas

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Daidai1031/pathreview/commit/72ff229abf222e21c45b45471e2214fed405a217

**Reproduction summary:**
I ran the API locally and exercised both POST endpoints through the OpenAPI UI at
`localhost:8000/docs`. `POST /profiles` turned out to take `multipart/form-data`
with an undocumented `resume_file` upload, while `POST /reviews` takes JSON — yet
`docs/API.md` describes both with identical one-line entries and no request format
at all, so the two are indistinguishable to a reader.

**PLAN.md link:** https://github.com/Daidai1031/pathreview/blob/docs/89-add-post-request-body-schemas/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
The issue body says the response schemas are already documented, but `docs/API.md`
has neither requests nor responses — I need to confirm with the maintainer whether
responses are in scope. Separately, two of the error paths I tested return 500 for
what is clearly invalid client input; that looks like a bug in the handlers'
exception handling, but it is a code change and I don't think it belongs in this
docs issue. Third, PDF resume uploads always fail with "Failed to parse PDF
resume" — the handler passes raw bytes to `PyPDF2.PdfReader`, which needs a
file-like object. That leaves an open question for the docs themselves: should
`docs/API.md` list PDF as a supported resume format, when in practice it never
works? I plan to document the allowlist as the code intends it, add a note about
the current limitation, and open a separate issue for the bug.

---

### Reproduction detail

Everything below was observed against the API running locally at
`http://localhost:8000`. Bearer tokens are redacted.

#### What `docs/API.md` says today

The Profiles and Reviews sections in full:

```
### Profiles

`POST /profiles` — Create a profile with resume and GitHub username.
`GET /profiles/{profile_id}` — Retrieve a profile.
`DELETE /profiles/{profile_id}` — Delete a profile and associated data.

### Reviews

`POST /reviews` — Request a new portfolio review for a profile.
`GET /reviews/{review_id}` — Retrieve a completed review.
`GET /reviews` — List reviews for the authenticated user (paginated).
```

One line per endpoint. No content type, no field names, no required/optional
information, no example request, and no mention that a bearer token is needed.
A reader cannot construct a valid request from this.

#### `POST /profiles` takes `multipart/form-data`, not JSON

```
curl -X 'POST' \
  'http://localhost:8000/profiles' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: multipart/form-data' \
  -F 'github_username=daidai1031' \
  -F 'portfolio_url=https://www.daidingrdesigns.com/' \
  -F 'resume_file='
```

`200 OK`:

```json
{
  "id": "39539042-b11e-4fa1-9f7a-068398cba5eb",
  "user_id": "cc258f35-98a3-457b-b1bb-6fec6c95f9a9",
  "github_username": "daidai1031",
  "portfolio_url": "https://www.daidingrdesigns.com/",
  "created_at": "2026-07-24T05:31:40.029680Z",
  "resume_filename": null
}
```

Three things here appear nowhere in `docs/API.md`:

1. The content type is `multipart/form-data`. The doc gives no reason to expect
   this; the default assumption for a POST endpoint is JSON.
2. There is a third field, `resume_file`, a file upload. The doc mentions "resume"
   in prose but never names the field or says it is a file.
3. The endpoint requires `Authorization: Bearer <token>` from `POST /auth/login`.

Source of truth: `create_profile_endpoint` in `api/routes/profiles.py`, whose
parameters are declared as `Form(default=None)` and `UploadFile = File(default=None)`.
`ProfileCreate` is constructed inside the handler; it is not the request body model.

#### `POST /reviews` takes `application/json`

Request body, marked **required** in the OpenAPI schema:

```json
{
  "profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

With a `profile_id` that exists, `200 OK` and the review is created with
`status: "pending"`; the analysis then runs in the background:

```json
{
  "id": "4be36d29-a966-418d-ac6b-080e0268081d",
  "profile_id": "39539042-b11e-4fa1-9f7a-068398cba5eb",
  "status": "pending",
  "sections": null,
  "overall_score": null,
  "error_message": null,
  "created_at": "2026-07-24T06:06:45.606040Z",
  "updated_at": "2026-07-24T06:06:45.606046Z"
}
```

Source of truth: `create_review_endpoint` in `api/routes/reviews.py` takes
`data: ReviewCreate`; `ReviewCreate` in `api/schemas/review.py` declares one
required field, `profile_id: UUID`.

#### Error responses — observed, not assumed

| Scenario | Status | Response body |
| --- | --- | --- |
| `POST /profiles` with no bearer token | 401 | `{"detail": "Not authenticated"}` |
| `POST /profiles` with a `.docx` resume | 422 | `{"detail": "Resume must be a PDF or Markdown file"}` |
| `POST /profiles` with a valid PDF resume | 422 | `{"detail": "Failed to parse PDF resume"}` |
| `POST /profiles` with a Markdown resume | 200 | profile created, `resume_filename` populated |
| `POST /profiles` with `github_username` over 255 chars | 500 | `{"detail": "Failed to create profile"}` |
| `POST /reviews` with a nonexistent `profile_id` | 500 | `{"detail": "Failed to create review"}` |

The 401 also carries a `www-authenticate: Bearer` response header. Swagger labels
all four as *Undocumented*, so they are missing from the OpenAPI schema as well as
from `docs/API.md`.

**On the two 500s.** Both are caused by invalid client input and would normally be
4xx. In `api/routes/profiles.py`, an over-length `github_username` arrives as an
unconstrained `Form` string and only fails when `ProfileCreate(...)` is constructed
inside the handler; that `ValidationError` is swallowed by the handler's generic
`except Exception` and re-raised as a 500. `api/routes/reviews.py` does the same
for a `profile_id` with no matching row.

The `.docx` case is the instructive contrast: that check raises `HTTPException`
explicitly, and the `except HTTPException: raise` branch passes it through intact,
so it correctly surfaces as 422. Two error paths in the same function, handled
differently.

Fixing the 500s is a code change and outside the scope of #89. I will document the
behavior as it currently stands, flag the discrepancy in the PR, and suggest a
separate issue.

#### PDF resume uploads always fail

Uploading a valid PDF returns 422:

```json
{
  "detail": "Failed to parse PDF resume"
}
```

Uploading Markdown succeeds:

```json
{
  "id": "a5cbcb29-6bf0-4373-80a0-e26a6fe9a854",
  "user_id": "cc258f35-98a3-457b-b1bb-6fec6c95f9a9",
  "github_username": "daidai1031",
  "portfolio_url": "https://www.daidingrdesigns.com/",
  "created_at": "2026-07-24T07:30:51.364782Z",
  "resume_filename": "001-chunking-strategy.md"
}
```

The two branches diverge in `create_profile_endpoint` (`api/routes/profiles.py`).
Both start from `content = await resume_file.read()`, which returns `bytes`. The
Markdown branch calls `content.decode("utf-8")`, which works on bytes. The PDF
branch calls `PyPDF2.PdfReader(content)`, but `PdfReader` expects a file path or a
file-like object — `bytes` has no `.seek()`, so the call raises, the surrounding
`except Exception` catches it, and every PDF becomes a 422. Wrapping the bytes,
`PdfReader(io.BytesIO(content))`, would be the usual fix.

The practical effect is that the API advertises PDF support — the type allowlist
accepts `application/pdf` and the rejection message names PDF first — while no PDF
has ever been accepted. This is a code bug, not a docs bug, so it is outside the
scope of #89. I searched the tracker and found no existing report; the closest is
the closed #76, which covered the related 500-vs-422 behavior for non-PDF files.
I plan to raise this separately rather than fold it into this PR.

#### Why this counts as a reproduction

The two POST endpoints take different content types — one form-data with a file
upload, one JSON — and `docs/API.md` describes them with structurally identical
one-line entries that omit the distinction entirely. A developer working from the
documentation alone cannot tell them apart, and the natural guess for `/profiles`
is wrong. All four error responses are undocumented as well.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–2 from PLAN.md were already done in Week 8 (confirming the wire format
for both endpoints and verifying the error paths against a running server). This
week I completed sub-tasks 3–5: the `POST /profiles` request section in
`docs/API.md` (content type `multipart/form-data`, a field table for
`github_username`, `portfolio_url`, and the previously undocumented `resume_file`
upload, plus a `curl -F` example), the `POST /reviews` request section
(`application/json`, required `profile_id`, JSON and curl examples), and the
authentication and error-response tables for both endpoints. I also recorded a
baseline of the repo's existing failures before touching anything —
53 failed / 375 passed on `make test-unit`, 182 ruff errors, 52 files unformatted
under black, 5 mypy errors — so I can prove my change doesn't add to them.

**Next steps:**
Add a test that guards the new documentation against drifting from the request
models, re-run the full check suite to confirm the failure counts are unchanged,
open a draft PR, and get peer feedback before marking it ready for review.

**Blockers:**
No hard blockers. Three scope questions remain open, and rather than wait on the
maintainer I decided to keep the change minimal and surface each one in the PR
description: (1) the issue body claims response schemas are already documented,
but `docs/API.md` has neither requests nor responses — I documented requests only,
matching the issue title; (2) two error paths return 500 for invalid client input
where a 4xx is expected; (3) PDF resume uploads always fail because
`create_profile_endpoint` passes raw bytes to `PyPDF2.PdfReader`. Both (2) and (3)
are code defects outside a docs issue, so I documented the observed behavior and
flagged them for the reviewer instead of widening the diff.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/685

**Branch:** `docs/89-add-post-request-body-schemas`

**What you built:**
Added request-body documentation for both POST endpoints to `docs/API.md`, which
previously described every endpoint with a single line and no request information
at all. Each endpoint now has its content type, a field table with types and
required/optional marking, a verified `curl` example, and a table of the error
responses it actually returns — all observed against a locally running server
rather than inferred from the source.

**Tests added or updated:**
Created `tests/unit/test_api_docs.py` with two tests that guard the documentation
against drifting from the code it describes.
`test_api_doc_documents_all_profile_request_fields` reads the live signature of
`create_profile_endpoint` and asserts that each of its form fields
(`github_username`, `portfolio_url`, `resume_file`) is still both a handler
parameter and present in `docs/API.md`.
`test_api_doc_documents_all_review_request_fields` iterates
`ReviewCreate.model_fields` and asserts every declared field appears in the doc.
Either test fails if someone changes a request model without updating the API
reference. Both are marked `pytest.mark.unit` to match the project's marker
convention so they run under `make test-unit`; the suite went from 375 to 377
passing with the failure count unchanged at 53.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

(This repository has substantial pre-existing failures on `main`. Measured before
and after my change: `make test-unit` 53 failed / 375 passed → 53 failed / 377
passed; `ruff` 182 errors → 182 errors; `black --check` 52 files → 52 files;
`mypy` 5 errors → 5 errors. My change introduces no new failures, and the two
files I touched are clean under ruff and black individually. Full detail in the
PR's Notes for Reviewers.)

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection
### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Reviewer @ahmadzai38 approved the PR, noting the API documentation was clear
and that both new tests in `test_api_docs.py` passed locally. They flagged
one inline typo in `docs/API.md`: the `POST /profiles` description read
"sCreate a profile..." instead of "Create a profile...".

**How you responded:**
Fixed the typo in a follow-up commit (`docs(api): fix typo in POST /profiles
description`) and replied on the review thread confirming the fix. No other
changes were requested — the PR was already approved before the typo fix.

---

### Reflection

**What was harder than you expected?**
Scoping the change correctly, not writing it. Once I actually hit both
endpoints locally, I found three things beyond the missing schemas: two
error paths returning 500 instead of 4xx for invalid client input (an
over-length `github_username`, a nonexistent `profile_id`), and PDF resume
uploads failing 100% of the time because `create_profile_endpoint` passes
raw `bytes` to `PyPDF2.PdfReader` instead of wrapping it in
`io.BytesIO()`. All three were tempting to just fix inline — I had already
traced the exact line — but a docs-only issue isn't the place to widen the
diff with unrelated behavior changes. Deciding to document the current
behavior faithfully, flag each one explicitly in the PR, and leave the
actual fixes for separate issues took more judgment than the schema-writing
itself.

**What did you learn about working in a large codebase?**
That the issue description and the actual system can disagree, and you have
to verify against the running code, not the ticket. Issue #89 says response
schemas are "already documented," but `docs/API.md` had neither requests
nor responses for either endpoint — I only found that by reading the file
myself. Similarly, `POST /profiles` looks like a JSON endpoint from the doc
prose, but the handler in `api/routes/profiles.py` declares its parameters
as `Form(...)` and `UploadFile`, and only builds a `ProfileCreate` object
internally — it's never the request body model. In a solo project I'd never
hit that gap between "what the code implies" and "what a Pydantic model at
the route boundary" actually is, because I'd always be the one who wrote
both.

**How did AI tools help — and where did they fall short?**
AI was most useful for structure: scaffolding `PLAN.md`, drafting the field
tables and `curl` examples once I told it the exact wire format, and
suggesting the drift-detection pattern for `tests/unit/test_api_docs.py`
(reading `create_profile_endpoint`'s live signature and `ReviewCreate.model_fields`
instead of hardcoding field names). It fell short anywhere that required
actually running the server — the multipart-vs-JSON distinction, the four
undocumented error responses, and the PDF bug were only found by sending
real requests to `localhost:8000` and reading real responses; no amount of
reading the route file would have surfaced that `PdfReader(bytes)` fails
because `bytes` has no `.seek()` without actually triggering the exception.

**What would you do differently if you started over?**
I'd raise the three scope questions (missing response docs, the 500s, the
PDF bug) with a mentor as soon as I found them in Week 8, instead of
resolving all three unilaterally and only surfacing them in the PR
description. They were reasonable calls, but for a first large-codebase
contribution I'd rather have a second opinion on "does this belong in my
PR" before committing to an answer, especially since the issue estimated
2–3 hours and the actual reproduction work — hitting every endpoint,
diffing four error paths, tracing the PDF bug to its exact line — took
considerably longer than that.

**What are you most proud of from this module?**
The two tests in `test_api_docs.py`, not the documentation itself. Most
docs-only PRs have no way to stay correct once the code changes again;
mine reads `create_profile_endpoint`'s actual signature and
`ReviewCreate.model_fields` at test time and fails if a field is added or
removed without the doc being updated. Turning a "just prose" issue into
something that's actually guarded by CI felt like the one place I went
beyond what the issue literally asked for.

