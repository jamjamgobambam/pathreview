## Solution plan

**Issue:**  https://github.com/ascherj/pathreview/issues/117 

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The current API documentation describes the available endpoints, but it does not provide executable `curl` examples that developers can use to test the API from the command line. The expected behavior is for the documentation to include clear, copy-and-paste examples demonstrating how to call the endpoints with the correct HTTP method, headers, and request body.

### Map
Which files, functions, or modules are involved?

- docs/api.md' - API documentation


### Plan
What are the steps to fix this issue?
1. Review `docs/api.md` and identify the endpoints that need `curl` examples.
2. Inspect the API implementation to confirm the correct HTTP methods, URLs, headers, and request body formats.
3. Add complete `curl` examples for the appropriate endpoints using consistent Markdown formatting.
4. Review the updated documentation to ensure the examples are accurate, easy to read, and match the current API implementation.
5. Verify that the documentation renders correctly and that the examples can be copied directly from the page.


### Inputs & outputs
What does your fix take as input? What should it produce or change?
Input :
    - Existing 'docs/api.md' documentation
    - API Endpoint definitions from the backend  

Output:
    - Updated API documentation containing complete and accurate `curl` examples 
    - Documentation that is easier for developers to test manually

### Risks & unknowns
What could go wrong? What are you still unsure about?
- Some endpoints may require authentication, so the examples may need placeholder JWT tokens.
- The request body shown in the examples must exactly match the current API schema.
- If endpoint definitions change, the documentation must be updated accordingly.

### Edge cases
What inputs or states should your fix handle gracefully?

- GET endpoints that do not require a request body.
- POST endpoints that require JSON payloads.
- Endpoints requiring Authorization headers.
- Placeholder values (IDs, tokens, usernames) should be clearly identified so users know what to replace.