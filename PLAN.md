# Solution Plan

**Issue:** POST /reviews endpoint has no test for when the profile has no ingested documents

Issue link: https://github.com/ascherj/pathreview/issues/88

---

## Understand

The issue is not that the endpoint itself is known to be broken, but that an important edge case is not covered by automated tests. When a review is requested for a profile that has no ingested documents, the endpoint should return an appropriate client error instead of crashing or returning a generic server error. Without this test, future code changes could unintentionally change the endpoint's behavior without being detected.

---

## Map

Files involved:

- `api/routes/reviews.py`
- `core/services/review_service.py`
- `tests/unit/test_review_routes.py`

---

## Plan

1. Understand the review creation flow from the route into the review service.
2. Identify where the missing-documents condition should be handled.
3. Add a focused unit test covering the missing edge case.
4. Verify that the endpoint returns the expected error instead of a generic failure.
5. Run the relevant unit tests and ensure the new test passes.

---

## Inputs & outputs

**Input**

- A request to create a review for a profile.
- A profile that has no ingested documents.

**Expected output**

- The endpoint returns the appropriate HTTP error.
- The new automated test verifies this behavior and prevents regressions.

---

## Risks & unknowns

- It is not yet clear whether the project expects a pure route unit test or a more integrated test exercising the complete review creation flow.
- The missing validation may already exist inside the service layer, requiring only additional test coverage.
- Existing testing conventions may require a different mocking strategy than initially expected.

---

## Edge cases

- Profile exists but has no ingested documents.
- Profile does not exist.
- Review creation succeeds normally.
- Unexpected internal exceptions should still return the appropriate server error.