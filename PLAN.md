

## Solution plan

**Issue:**
<!-- [issue title and link] -->
POST /reviews endpoint has no test for when the profile has no ingested documents #88

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?
The root cause of the issue is hardcoded sections regardless of inputs, does not allow the system to raise an error. The endpoint should return a 4xx error when a profile has no ingested documents The actual behavior is that the system silently accepts a profile with no source documents and completes the review with hardcoded content — it neither raises an error nor crashes.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.
The files to be touched:\
`/tests/unit` \
`/core/services/review_service.py`\
`api/routes/reviews.py` with functions:

- `create_review_endpoint()`
- `create_review()`

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
The expected behavior of the system is to add a test that verifies the endpoint returns an appropriate error rather than crashing when a profile has no source documents. To complete this:

1. Would need to fetch the Profile before creating the review. In create_review() or in create_review_endpoint() before calling it — query the Profile by profile_id so its github_username, portfolio_url, and resume_text fields are available to check. As observed, currently create_review() never touches the profile at all.
2. Add the no-documents check and raise an error. If github_username, portfolio_url, and resume_text are all falsy, raise HTTPException(status_code=400, detail="Profile has no ingested documents to review") from create_review_endpoint. before background_tasks.add_task(process_review, ...)the check has to happen before scheduling, since the client response is already sent once the background task is queued.
3. Write the failing-case unit test. In tests/unit/test_review_service.py, add a test with a mock Profile where github_username, portfolio_url, and resume_text are all None/empty, asserting the endpoint/service raises the 400 rather than returning a Review with status="pending".
4. Write a regression test for the happy path. Add a test with at least one field populated (e.g., github_username set) confirming create_review still succeeds and schedules processing as before — this guards against the new check accidentally blocking valid profiles.

### Inputs & outputs

What does your fix take as input? What should it produce or change?
The fix should take an input of a POST/review request with profile_id and  that fetches a github repo name, portfolio_url, and resume documentation associated with it.  An input with documents should produce unchanged Review with a status of pending and 200 response. The output, if all 3 are falsy, should raise a HTTPException(400, "Profile has no ingested documents to review") instead of creating a review. If at least one is set, the output should be unchanged, Review with a status of pending and 200 response.

### Risks & unknowns

What could go wrong? What are you still unsure about?

- Unresolved: should the no-documents check live in create_review() (breaks ~6 existing unit tests that call it directly without mocking a Profile fetch) or in create_review_endpoint()?
- The check must raise HTTPException specifically (else the route's generic exception handler converts it to a 500) and must run before create_review() commits the row (else a rejected request leaves an orphaned "pending" review).

### Edge cases

What inputs or states should your fix handle gracefully?

The fix should handle nonexistent profile_id, whitespace-only and blank string values gracefully. The profile-fetch step must handle both a profile_id that doesn't resolve to any Profile 

- should 404, not the 400 "no documents" message

 and a Profile whose fields are whitespace-only or empty strings rather than None

- .strip() before the truthiness check, since nothing at the DB level prevents "   " from being saved as github_username/portfolio_url/resume_text
