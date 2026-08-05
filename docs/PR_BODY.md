## Summary
This PR adds comprehensive request body schema documentation for the POST /profiles and POST /reviews endpoints in the API reference documentation. Previously, the docs only provided one-line descriptions without detailing the request structure, making it difficult for frontend developers to use these endpoints.

## Issue
Closes #89

## Changes
- Added detailed request body schema for POST /profiles with multipart/form-data format
  - Field table with types, requirements, and descriptions (github_username, portfolio_url, resume_file)
  - Validation rules including file type restrictions (PDF/Markdown only)
  - Example curl request with proper headers and form fields
  - Example response JSON with ProfileResponse structure
- Added detailed request body schema for POST /reviews with JSON format
  - Field table documenting profile_id (UUID, required)
  - Error response documentation (404, 422)
  - Example curl request with JSON payload
  - Example response JSON with ReviewResponse structure showing pending status
- All documentation verified against actual implementation (api/routes/profiles.py, api/routes/reviews.py, and Pydantic schemas)

## Testing
- [x] Unit tests pass (`make test-unit`) - N/A: Documentation-only change, no code modifications
- [x] Integration tests pass (`make test-integration`) - N/A: Documentation-only change
- [x] Linter passes (`make lint`) - N/A: Cannot run (no venv setup in environment)
- [x] Type checker passes (`make typecheck`) - N/A: Cannot run (no venv setup in environment)
- [x] New/updated tests cover the changes - N/A: Documentation-only change requires no tests

**Note:** This is a documentation-only change with no code modifications. The environment does not have .venv setup, so make commands cannot run, but this does not affect the validity of the documentation changes. All content was manually verified against the source code.

## Screenshots / Demo
N/A - Documentation change only. The updated docs can be viewed in docs/API.md.

## Notes for Reviewers
- Please verify that the documented field types and constraints match the actual implementation in:
  - api/routes/profiles.py (lines 24-30, 40-53 for validation)
  - api/schemas/profile.py (lines 7-10)
  - api/routes/reviews.py (lines 22-28)
  - api/schemas/review.py (lines 14-15)
- The curl examples use realistic UUIDs and demonstrate proper header usage
- Error responses are documented based on HTTPException blocks in the route handlers
- This is a Tier 1 issue from the course project
