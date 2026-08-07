## Solution plan

**Issue:** [`POST /reviews` endpoint has no test for when the profile has no ingested documents](https://github.com/ascherj/pathreview/issues/88)

### Understand
The `POST /reviews` endpoint has no test covering a valid profile with no
associated ingested content. The endpoint currently creates a pending review
and schedules background processing without first checking whether there is
content available to review. The expected behavior described by the issue is a
controlled client error rather than creating a review or crashing.

### Map
The main file to add is `tests/unit/test_review_routes.py`.

The behavior under test is implemented by `create_review_endpoint` in
`api/routes/reviews.py`. Its dependencies include `create_review` and
`process_review` from `core/services/review_service.py`, `get_current_user`,
`get_db`, and FastAPI's `BackgroundTasks`.

### Plan
1. Confirm the intended HTTP status code and error message for a profile with
   no ingested content.
2. Add route-test fixtures for an authenticated user, an empty profile, a
   mocked database session, and background tasks.
3. Add a test that calls `POST /reviews` with the empty profile's ID and
   verifies that the endpoint returns the agreed controlled error.
4. Verify that the failure path does not create a review, commit database
   changes, or schedule `process_review`.
5. Run the focused route test and the full unit-test suite to check for
   regressions.

### Inputs & outputs
The input is an authenticated `POST /reviews` request containing the ID of a
valid profile that has no associated ingested content. The expected output is
a stable 4xx response with a clear error message. No review record or
background processing task should be created.

### Risks & unknowns
The issue does not specify the exact status code or response message. It is
also unclear whether "no ingested documents" means no `IngestedSource` database
rows or no source material—such as a resume, GitHub username, or portfolio
URL—available for ingestion. Current review processing performs ingestion
after the review is created, so requiring pre-existing `IngestedSource` rows
may conflict with the existing workflow. The endpoint currently has no
validation for either interpretation, so a test expecting a 4xx response will
fail until the intended production behavior is confirmed or implemented.

### Edge cases
The test should distinguish an existing empty profile from a nonexistent
profile, a profile owned by another user, and a profile that has valid content.
It should also ensure that the empty-profile failure does not accidentally
return a generic 500 response or schedule background work.
