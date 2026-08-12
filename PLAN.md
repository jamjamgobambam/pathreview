# Solution Plan

## Issue

POST /reviews endpoint has no test for when the profile has no ingested documents

https://github.com/ascherj/pathreview/issues/88

---

## Understand

Issue #88 identifies a missing unit test for the review creation flow when a valid profile exists but has no ingested documents. The issue description references `tests/unit/test_review_routes.py`, but that file is no longer present in the current repository. After investigating the current codebase, I found that review-related tests now exist in `tests/unit/test_review_service.py`. The expected behavior is that attempting to create a review for a profile without ingested documents should return an appropriate error instead of failing unexpectedly.

---

## Map

Files involved:

- tests/unit/test_review_service.py
- core/services/review_service.py
- api/routes/reviews.py

---

## Plan

1. Review the existing review creation tests in `tests/unit/test_review_service.py`.
2. Determine how the review service handles profiles without ingested documents.
3. Add a new unit test covering this missing scenario.
4. Verify the expected error response or exception.
5. Run the test suite to ensure the new test passes and existing tests continue to pass.

---

## Inputs & Outputs

Input:
- Valid profile ID
- Profile without ingested documents

Output:
- Appropriate error response
- New unit test validating the behavior

---

## Risks & Unknowns

- The expected error type or HTTP status code may need to be confirmed.
- The repository structure has changed since the issue was opened, so the original file path is no longer valid.
- Additional fixtures may be required to create a profile with no ingested documents.

---

## Edge Cases

- Profile exists but has no ingested documents.
- Invalid profile ID.
- Missing user permissions.
- Empty ingestion results.