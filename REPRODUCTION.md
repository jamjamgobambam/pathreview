# Reproduction of Issue #117

## Issue
API docs in `docs/API.md` list endpoints but contain no example `curl` commands.

## Reproduction Steps
1. Open `docs/API.md` in the repository
2. Observe that each endpoint is listed with:
   - HTTP method and path (e.g., `POST /auth/register`)
   - Brief description
   - No `curl` command examples
3. Visit `http://localhost:8000/docs` (Swagger UI) to see the actual API
4. Confirm that `curl` examples are missing from the documentation

## Expected Behavior
Each endpoint should have a copy-pasteable `curl` example that works with the local API.

## Current Behavior
No `curl` examples are present in `docs/API.md`.