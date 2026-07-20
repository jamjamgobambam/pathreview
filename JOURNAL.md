# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API reference lists the profile and review creation endpoints but does not explain the data each endpoint accepts. This makes it unclear that `POST /profiles` uses multipart form data with optional profile fields and a resume upload, while `POST /reviews` expects JSON containing a required profile UUID. The change affects `docs/API.md` and uses the existing FastAPI routes and Pydantic schemas as the source of truth. A successful fix documents both request schemas with field types, requirements, constraints, descriptions, and example values.

**Branch name:** `docs/issue-89-request-schemas`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### “Is this right for me?” checklist reasoning

- The issue is labeled Tier 1 and has a focused, one-file documentation scope.
- The expected result is clear: document both POST request formats without changing application behavior.
- The relevant implementation is available in `api/routes/profiles.py`, `api/schemas/profile.py`, and `api/schemas/review.py`, so every documented field can be verified against code.
- The work can be validated by reviewing the generated Markdown, checking the Git diff, and running the repository checks.
- The main scope risk is describing `POST /profiles` as JSON even though it uses `multipart/form-data`; the draft explicitly documents the correct content type.

### Setup notes

- Cloned the personal fork and configured `origin` and `upstream` remotes.
- Installed Docker Desktop, WSL 2, GNU Make, Python 3.11, and project dependencies.
- Ran `make setup` successfully, including database migrations and seed data.
- Ran `make run`; the frontend loaded at `http://localhost:5173` and the API responded at `http://localhost:8000`.
