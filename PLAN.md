# Solution Plan

**Issue**

API docs don't include example curl commands

https://github.com/ascherj/pathreview/issues/117

## Understand

The API documentation lists all available endpoints but does not provide 
example curl commands. Developers must manually determine request 
methods, headers, and JSON payloads before testing the API. Adding copy 
and paste examples will make onboarding much easier.


## Map

Files involved:

- docs/API.md

Reference files:

- api/routes/
- README.md
- OpenAPI documentation at localhost:8000/docs

## Plan

1. Review api/routes/auth.py to determine the exact request format for 
/auth/register and /auth/login.
2. Inspect the authentication implementation to confirm how Bearer 
tokens should be included in authenticated curl examples.
3. Review the profile routes and schemas to determine whether requests 
require JSON, form data, or file uploads.
4. Write tested curl examples for every documented endpoint in 
docs/API.md.
5. Verify each example against the local server and ensure the 
documentation formatting remains consistent.


## Inputs & Outputs

Input:

Current API documentation.

Output:

Updated documentation with complete curl examples for every endpoint.


## Risks & Unknowns

- Some endpoints require authentication tokens: api/routes/auth.py may 
require different request formats for registration and login, so I need 
to verify the expected content type before writing examples.
- Need to verify exact JSON payloads: api/routes/auth.py may require 
different request formats for registration and login, so I need to 
verify the expected content type before writing examples.
- Endpoint paths may differ from assumptions: Authenticated endpoints 
require a Bearer token, so I need to determine the correct way to 
demonstrate token usage consistently across the documentation.

## Edge Cases

- Login endpoint requires form-encoded data rather than JSON.
- Profile creation may include uploaded files as multipart form data.
- Authenticated requests must demonstrate a valid Authorization: Bearer 
<token> header.
- Example requests should work against a fresh local installation using 
http://localhost:8000.
- Placeholder IDs and tokens should be clearly marked so users know what 
to replace.
