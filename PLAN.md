## Solution plan

**Issue:** Add example API invocations to the documentation  
https://github.com/ascherj/pathreview/issues/117

### Understand
The API documentation currently lists each endpoint and its purpose but does not include example `curl` commands. This makes it harder for developers setting up the project to quickly test endpoints and verify that the API is working.

**Expected behavior:** The API documentation should provide example `curl` requests for each endpoint (or representative endpoints) so developers can easily interact with the API from the command line.

**Actual behavior:** The documentation only describes the endpoints without showing how to invoke them.

### Map
Files involved:
- `docs/API.md`

Sections expected to be updated:
- Health
- Authentication
- Profiles
- Reviews

### Plan
1. Review each documented endpoint and determine the appropriate HTTP method, URL, headers, and request body.
2. Add example `curl` commands for each endpoint, including JSON payloads where applicable.
3. Include authentication headers (`Authorization: Bearer <token>`) for endpoints that require a logged-in user.
4. Verify that the examples are consistent with the documented endpoint paths and request formats.
5. Review the updated documentation for readability and formatting consistency.

### Inputs & outputs
**Inputs:**
- Existing endpoint definitions in `docs/API.md`
- API routes and expected request formats

**Outputs:**
- Updated `docs/API.md` containing example `curl` commands that demonstrate how to invoke each endpoint and verify API functionality.

### Risks & unknowns
- Some endpoints may require authentication or resources created by previous requests, so example commands may need placeholder values (e.g., `<token>`, `<profile_id>`, `<review_id>`).
- The exact request body fields may need to be confirmed against the API implementation to ensure the examples are accurate.

### Edge cases
- Clearly indicate placeholder values that users must replace before running commands.
- Ensure examples for authenticated endpoints include the required authorization header.
- Use valid JSON formatting in request bodies.
- Keep examples consistent with the documented base URL (`http://localhost:8000`).
