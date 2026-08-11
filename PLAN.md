## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/117

# PLAN.md

## Understand

The root cause of this issue is that `docs/API.md` describes the available API endpoints but only explains them conceptually. It does not include complete example commands showing how to call those endpoints.
The expected behavior is that a developer setting up the project for the first time can copy an example `curl` command, run it against the local API, and confirm that the endpoint works.
The actual behavior is that developers must determine the correct URL, HTTP method, headers, and JSON request body themselves.

## Map

The main file involved is:

* `docs/API.md`

I will also review the implementation of the documented API endpoints to confirm the correct routes, request fields, headers, and response behavior for the following endpoints:

* `POST /auth/register`
* `POST /auth/login`
* `POST /profiles` — Create a profile with a resume and GitHub username.
* `GET /profiles/{profile_id}` — Retrieve a profile.
* `DELETE /profiles/{profile_id}` — Delete a profile and its associated data.
* `POST /reviews` — Request a new portfolio review for a profile.
* `GET /reviews/{review_id}` — Retrieve a completed review.
* `GET /reviews` — List reviews for the authenticated user.

The primary file I expect to modify is:

* `docs/API.md`


The only file I currently expect to modify is:

- `docs/API.md`

## Plan

1. Review every endpoint documented in `docs/API.md` and create a list of the endpoints that need example `curl` commands.

2. Inspect the corresponding route and request-schema files to confirm the required HTTP methods, paths, headers, and JSON fields.

3. Run the application locally using `LLM_PROVIDER=mock` and manually test each planned `curl` command.

4. Add a clearly formatted example `curl` command under each endpoint in `docs/API.md`, including required headers and sample request bodies.

5. Review the updated documentation for consistency and rerun every example to confirm that the commands work as written.

## Inputs & outputs

### Inputs

The documentation examples will use:

- The local API base URL and port
- The endpoint path
- The required HTTP method
- Required headers, such as `Content-Type: application/json`
- Example JSON request data
- Authentication tokens for endpoints that require authorization

### Outputs

The fix will update `docs/API.md` with copyable `curl` examples for the documented endpoints.

Running an example should produce a successful authentication, reviews and profiles API endpoints

This change will not modify the API's runtime behavior. It will only improve the documentation.

## Risks & unknowns

- The local API port or base URL may differ depending on how the project is started. I will verify the default value from the project configuration and README.

- Example commands may behave differently in PowerShell, Command Prompt, and Unix-style terminals because quoting rules differ. I will use the command format that matches the project's existing documentation style.

## Edge cases

- Registering with an email address or username that already exists
- Sending a request with a missing required field
- Sending malformed JSON
- Using an invalid email address
