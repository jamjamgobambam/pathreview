## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/88, OST /reviews endpoint has no test for when the profile has no ingested documents

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

There should be a test for the POST / reviews that verifies it returns an appropriate error when the profile's source fields (GitHub username, Resume, Portfolio URL) are empty.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

There should be an added test in tests/unit/test_review_routes.py

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Trace the "review" path from the route to the service, to find where "no ingested documents" should be detected.

2. Define what counts as "no ingested documents" for a review, and what error and message should be returned.

3. Write the test that recreates the empty-profile case and checks the endpoint response. The test should create a profile that exists but has no source data, then call the review endpoint and assert it against the expected error and message.

4. Run this test to confirm whether or not the endpoint handles the empty profile case properly.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

The inputs to the test: authenticated user, user's profile record, profile that has no ingestable content fields set (no GitHub username, resume file, or portfolio URL), and the POST /reviews request body containing that profile's profile_id

The expected output of the test should be the assertion: whether the endpoint returns the expected error response instead of crashing.

### Risks & unknowns
What could go wrong? What are you still unsure about?

### Edge cases
What inputs or states should your fix handle gracefully?