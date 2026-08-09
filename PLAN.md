## Solution plan

**Issue:** [``POST /reviews`` endpoint has no test for when the profile has no ingested documents](https://github.com/ascherj/pathreview/issues/88)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- The root cause is just that there is no unit test for this specific endpoint with that input yet. The expected behavior for this endpoint-level test is that the endpoint should handle this edge case gracefully by not creating a review with no ingested sources and returning an appropriate error response. The current actual behavior is that the request is accepted, a review is still created even with no documents or sources and completes the review with generic analysis.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
1. `tests/unit/test_review_routes.py`: creating a separate file for this endpoint-level testing
2. `api/routes/reviews.py`: where the `POST /reviews` request routes to that needs to be tested
3. `core/services/review_service.py`: contains backend functions and processes that are called when a request is accepted by `POST /reviews`
4. `tests/unit/`: contains all of the existing testing files to follow similar structure

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Review the current existing tests in the `tests/unit/` folder to understand and match the structure of the pytest patterns and fixtures.
2. Set up a test user and a profile that has no data sources (Github, Resume, Portfolio) and ingested documents yet.
3. Send a ``POST /reviews`` request with the empty profile's ID.
4. Assert that the endpoint handles a request with a profile that no sources gracefully with the expected error response.
4. Run the pytest to ensure the test case runs properly (fixing the feature if the test case fails is outside of the scope.)

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- Input: an authenticated (using login token and profile ID) `POST /reviews` request for a profile that has no Github username, resume, nor portfolio.
- Output: A new pytest test case file that covers this edge case at the endpoint level, verifying that the endpoint handles it gracefully.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- The expected behavior for this edge case doesn't seem to be defined yet. Is the endpoint supposed to return an error response? If so, what status code or message will it have?
- 

### Edge cases
What inputs or states should your fix handle gracefully?
- A profile that has no Github username, portfolio URL, nor uploaded resume associated to it.
- A profile that has the source fields, but ingestion produces no documents to create a review from.