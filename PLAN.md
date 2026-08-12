# PLAN

## Solution plan

**Issue:** [API docs don't include example curl commands](https://github.com/ascherj/pathreview/issues/117)

### Understand

The current API documentation describes the available endpoints but does not include examples showing how to call them with `curl`. Developers must inspect the source code or Swagger documentation to determine the correct request method, URL, headers, authentication, and body. A successful fix will provide accurate, copy-and-paste examples for the documented endpoints.

### Map

The main file I expect to change is:

- `docs/API.md`

I will also inspect:

- `api/` for route definitions
- `core/` for configuration or authentication behavior
- Request and response models used by the API
- Swagger documentation at `http://localhost:8000/docs`

### Plan

1. Review every endpoint currently listed in `docs/API.md`.
2. Match each documented endpoint with its implementation in the `api/` directory.
3. Identify the required method, URL, headers, request body, path parameters, query parameters, and authentication.
4. Add a formatted `curl` example below each applicable endpoint.
5. Run each command against the local API and correct any inaccurate examples.

### Inputs & outputs

The inputs are the current API documentation, backend route definitions, request schemas, and local API behavior.

The output will be an updated `docs/API.md` containing tested `curl` examples that developers can copy and run locally.

### Risks & unknowns

- Some endpoints may require authentication tokens.
- The API documentation may contain outdated paths or request formats.
- Some examples may depend on seeded database records.
- Quoting and line continuation may differ between Git Bash, PowerShell, and Command Prompt.
- I need to confirm whether every endpoint needs an example or only the most commonly used endpoints.

### Edge cases

- Endpoints requiring authentication must show the correct authorization header.
- Examples must use valid JSON field names and data types.
- Path and query parameter examples must use realistic placeholder values.
- Commands must not expose real passwords, tokens, or API keys.
- Examples should clearly show which values developers need to replace.
- Commands should use the correct local API URL and port.