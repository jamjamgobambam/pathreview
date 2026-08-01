## Solution plan

**Issue:** `POST /reviews` endpoint has no test for when the profile has no ingested documents — https://github.com/ascherj/pathreview/issues/88

### Understand
This is a feature gap, not a crash-causing bug, nothing throws or breaks, but the endpoint has no precondition check for whether a profile has any ingested content before generating a review.

From reproducing the bug, I found that create_review creates the review and starts the background task without checking whether the profile has any ingested content.

From there, `_run_agent_orchestration` and `_run_rag_retrieval_generation` still return the same placeholder feedback even when the ingestion step returns an empty list. Since `_run_safety_checks` only verifies that the response has the expected format, it doesn't catch that the feedback wasn't generated from any real profile data.

Expected behavior: `POST /reviews` should reject (or the background task should fail) when a profile has zero ingested sources, with a clear error rather than a silently "complete" review full of fake data.

Actual behavior: the review always completes successfully with the same canned feedback, regardless of ingested content.

### Map
- `api/routes/reviews.py` — create_review_endpoint (possible place to validate that the profile has ingested content)

- `core/services/review_service.py` — create_review, process_review, and _run_ingestion_pipeline

- `core/models/ingested_source.py` — model used to check whether a profile has any ingested sources

- `tests/unit/test_review_routes.py` — new test file to cover the missing case described in the issue

### Plan
1. Add a query in `create_review` (or the endpoint, before calling `create_review`) that checks for at least one `IngestedSource` row for the profile.

2. If none exist, raise `HTTPException(400, detail="Profile has no ingested content")` before creating the review row or scheduling `process_review`.

3. Create `tests/unit/test_review_routes.py` with a test that mocks the DB to return zero ingested sources and asserts the endpoint returns 400 instead of creating a review.

4. Add a second test confirming the happy path (profile with at least one ingestd source) still creates a 'pending' review as before, to guard against regressions.

5. (Stretch) Add a service-layer unit test confirming `_run_agent_orchestration`/`_run_rag_retrieval_generation` are never reached when sources are empty, once the guard is in place.

### Inputs & outputs
Input: `POST /reviews` body `{profile_id, user_id}` for a profile with no `IngestedSource` rows.

Expected output: `400 Bad Request` with a clear `detail` message or no `Review` row created or no background task scheduled.

### Risks & unknowns
- I still need to confirm whether "no ingested content" should also cover a profile that has sources but they're empty/malformed, or strictly "zero rows" 
— issue title says "no ingested documents," so starting with the zero-row case.

- Adding this check changes existing behavior (previously always succeeded) — need to check the frontend handles a 400 response on submission gracefully rather than assuming every POST succeeds.

- Where to add the check may affect the transaction boundary — want to avoid a partial commit if the check itself needs a query but the review creation is in a separate call.

### Edge cases
- A profile has a GitHub username or other information, but ingestion fails and no sources are produced. That would still leave the pipeline with nothing to analyze, although handling that scenario may be outside the scope of this issue.

- If two requests happen at the same time, and ingested content is added between the validation check and review creation. That's a possible race condition, but it doesn't seem to be the main focus of this issue.