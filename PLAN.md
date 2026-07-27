## Solution plan

**Issue:** Resume upload silently dropped — profiles are always created with `resume_text=None` (found while tracing the profile-submission feature end-to-end)

### Understand
**Expected:** When a user submits the profile form with a resume file, the file is
uploaded, parsed, and its text stored on the profile (`resume_text`).

**Actual:** The resume never reaches the backend. The frontend appends the file
under the form field name `resume`, but the FastAPI route binds the upload to a
parameter named `resume_file`. FastAPI matches multipart fields to parameter
names, so `resume_file` is always `None`, the entire parsing block is dead code,
and every profile is persisted with `resume_filename=None` / `resume_text=None`.

There is no error — the request succeeds and a profile is returned — which is why
this is easy to miss. Client-side validation *requires* a resume, so users believe
it was uploaded.

Secondary defect (currently masked): even if a file did arrive, the PDF branch
calls `PyPDF2.PdfReader(content)` on raw `bytes`. `PdfReader` expects a file-like
stream, so it would need `io.BytesIO(content)`. This line is never reached today
because of the field-name mismatch above.

Architectural note (not a bug, but a doc/code mismatch worth recording): the
resume is parsed *inline in the route handler* and stored as a raw `Text` column
in Postgres. It does **not** flow through the `ingestion/` pipeline
(parse → chunk → embed → store) that `docs/ARCHITECTURE.md` describes. That
pipeline is not invoked anywhere in the profile-creation path.

### Map
End-to-end trace of "user submits a profile with a resume":

1. Form — [frontend/src/components/ProfileForm.tsx:39-59](frontend/src/components/ProfileForm.tsx#L39-L59)
   — builds `FormData`; appends file as `resume` at [line 48](frontend/src/components/ProfileForm.tsx#L48).
2. Hook — [frontend/src/hooks/useProfileSubmit.ts:15-29](frontend/src/hooks/useProfileSubmit.ts#L15-L29)
   — calls `apiClient.createProfile(formData)`.
3. API client — [frontend/src/services/api.ts:73-89](frontend/src/services/api.ts#L73-L89)
   — `POST /api/profiles`, multipart body + Bearer token.
4. Route handler — [api/routes/profiles.py:23-98](api/routes/profiles.py#L23-L98)
   — expects `resume_file` at [line 27](api/routes/profiles.py#L27); MIME check + inline
   parse at [lines 40-76](api/routes/profiles.py#L40-L76) (PDF parse at [line 62](api/routes/profiles.py#L62)).
5. Service — [core/services/profile_service.py:13-33](core/services/profile_service.py#L13-L33)
   — constructs `Profile`, `add` / `commit` / `refresh`.
6. Model/DB — [core/models/profile.py:31-32](core/models/profile.py#L31-L32)
   — `resume_filename` (String) and `resume_text` (Text) columns in `profiles`.

**Files expected to touch:**
- [frontend/src/components/ProfileForm.tsx](frontend/src/components/ProfileForm.tsx) — field name `resume` → `resume_file`.
- [api/routes/profiles.py](api/routes/profiles.py) — wrap PDF bytes in `io.BytesIO` before `PdfReader`.
- [frontend/src/components/__tests__/ProfileForm.test.tsx](frontend/src/components/__tests__/ProfileForm.test.tsx) — assert the correct field name is sent.

### Plan
1. Align the field name: change `formData.append('resume', resumeFile)` to
   `'resume_file'` in `ProfileForm.tsx` (single source of truth is the FastAPI
   parameter name).
2. Fix the PDF parse: `PyPDF2.PdfReader(io.BytesIO(content))` and add `import io`.
3. Add/adjust a frontend test asserting the submitted `FormData` uses `resume_file`.
4. Add a backend test that posts a small PDF/markdown and asserts `resume_text`
   is persisted (guards against a future regression of either bug).
5. Manually verify end-to-end: submit a real PDF, confirm `resume_text` is
   non-null in the DB and echoed back in the response.

### Inputs & outputs
- **Input:** multipart form — `github_username` (str), optional `portfolio_url`
  (str), optional `resume_file` (PDF / Markdown / plain text, ≤10MB).
- **Output:** a persisted `Profile` row whose `resume_filename` and `resume_text`
  are populated when a resume is provided; `ProfileResponse` JSON returned to the
  client. No change to the response schema.

### Risks & unknowns
- Other callers may already depend on the current (broken) `resume` field name —
  grep for `'resume'` usages before renaming. Backend param rename would be more
  invasive, so prefer changing the frontend to match the backend.
- PyPDF2 version/behavior: confirm `PdfReader(BytesIO(...))` matches the installed
  version; some code uses the newer `pypdf` package name.
- Unclear whether resume text is *supposed* to be routed through `ingestion/`
  rather than stored inline. This fix keeps current behavior (inline Text column);
  routing through ingestion is a separate, larger design question.

### Edge cases
- No resume provided → profile still created with null resume fields (unchanged).
- Wrong MIME type → 422 (already handled at [profiles.py:44-53](api/routes/profiles.py#L44-L53)).
- Corrupt/unparseable PDF → 422 "Failed to parse PDF resume" (already handled).
- Empty PDF or PDF with no extractable text → `resume_text` may be empty string;
  decide whether to treat as null.
- Markdown / plain text with non-UTF-8 bytes → `content.decode("utf-8")` would
  raise; consider a decode fallback or explicit 422.
