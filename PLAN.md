## Solution plan

**Issue:** POST /reviews endpoint has no test for when the profile has no ingested documents
https://github.com/ascherj/pathreview/issues/88#top

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
The root cause of this issue is that the POST /reviews endpoint does not have a test for when a profile exists but has no associated ingested content. All cases must be tested and to ensure accuracy, there needs to be a test case. The expected behavior is that the endpoint returns a controlled error response instead of crashing.
### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
The main files and functions involved are:

- `api/routes/reviews.py` — contains the `create_review_endpoint` function for `POST /reviews`
- `core/services/review_service.py` — contains review creation and processing behavior
- `tests/unit/test_review_routes.py` — the route test file referenced by the issue; this file may need to be created
- `tests/conftest.py` — may contain fixtures or mocks needed for authentication and database dependencies

I only expect to use tests/unit/test_review_service.py as a reference for the project’s test style.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. First, I look at the create_review_endpoint and functions around this to observe and understand behavior. I might even use AI to help check my understanding. 
2. I will observe patterns in `tests/unit/test_review_service.py` to match with the test file I will make. 
3. I will add the test case for profile with no ingested and check that status code/error message are accurate and not crashing. 
4. I will run test and ensure it passes.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
Input:
Authenticated user
User profile
No documents
Request to POST /reviews

Output:
A clear error message
Correct HTTP status code
No crashing instead exception
Passing the test case

### Risks & unknowns
What could go wrong? What are you still unsure about?
I still need to confirm the exact status code and error message. Authentication and database dependencies may need to be mocked or overridden because I could not create a blank profile through the user interface. There are also unrelated failures in tests/unit/test_review_service.py, so I will run the new route test independently.

### Edge cases
What inputs or states should your fix handle gracefully?
The profile exists but has no associated ingested content. The endpoint returns the expected controlled error instead of crashing.
The authenticated user/profile setup is mocked correctly.