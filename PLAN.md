# Week 8 - Issue Reproduction & Solution Planning

## Issue

**Issue:** #89 - API reference doc is missing the `POST /profiles` request body schema

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Branch:** `docs/issue-89-request-schemas`

## Reproduction

### Expected Behavior

The API reference should document the request body for endpoints that create resources.

For `POST /profiles`, the docs should explain that the endpoint accepts `multipart/form-data` with fields for:

- GitHub username
- Portfolio URL
- Resume file upload

For `POST /reviews`, the docs should explain that the endpoint accepts JSON with a required `profile_id`.

### Actual Behavior

Before the fix, `docs/API.md` listed `POST /profiles` and `POST /reviews`, but did not document the request body fields, required/optional status, descriptions, or example values. A contributor reading only the API reference would not know what data to send to either endpoint.

### Steps to Reproduce

1. Open `docs/API.md`.
2. Find the profile endpoints section.
3. Confirm `POST /profiles` is listed.
4. Notice the request body schema is missing.
5. Find the review endpoints section.
6. Confirm `POST /reviews` is listed.
7. Notice the required `profile_id` JSON request body is missing.
8. Compare the docs with the backend source files:
   - `api/routes/profiles.py`
   - `api/schemas/profile.py`
   - `api/schemas/review.py`

## Root Cause

The backend already defines the expected request data, but the API reference only described the endpoints at a high level. The documentation was incomplete and did not expose the request schemas contributors need when calling the API.

## Solution Plan

### Files to Change

- `docs/API.md`
- `JOURNAL.md`

### Implementation Steps

1. Inspect `api/routes/profiles.py` to confirm the request format for `POST /profiles`.
2. Identify which fields are form values and which field is a file upload.
3. Inspect `api/schemas/review.py` to confirm the request format for `POST /reviews`.
4. Update `docs/API.md` with a `POST /profiles` request body section.
5. Document each `POST /profiles` field with type, required status, description, and example value.
6. Update `docs/API.md` with a `POST /reviews` request body section.
7. Document the required `profile_id` field as a UUID.
8. Add concise example request data for both endpoints.
9. Record issue selection, scope, branch, setup status, and planning notes in `JOURNAL.md`.

## Risks and Edge Cases

- `POST /profiles` must be documented as `multipart/form-data`, not JSON.
- Optional fields should not be described as required.
- The resume should be documented as a file upload, not a string path.
- `profile_id` should be documented as a required UUID for `POST /reviews`.
- The documentation should match the actual FastAPI route and Pydantic schemas, not only the issue description.
- Because this is a docs-only change, implementation should not modify API behavior or tests.

## Verification Plan

- Review `docs/API.md` and confirm both request schemas are present.
- Compare documented fields against `api/routes/profiles.py`, `api/schemas/profile.py`, and `api/schemas/review.py`.
- Confirm the Git diff only includes documentation/planning files.
- If the local environment is available, run the app and test suite checks.
- If local Docker setup is unavailable, document that verification is limited to source and documentation review.

