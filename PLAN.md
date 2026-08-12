# Solution Plan

**Issue:** POST /reviews endpoint has no test for when the profile has no ingested documents

Issue link: https://github.com/ascherj/pathreview/issues/88

---

## Understand

The issue is a gap in automated test coverage rather than a confirmed production bug. The `POST /reviews` endpoint currently creates a pending review and schedules background processing even when the profile has no resume, GitHub source, or portfolio content. The expected behavior is for this request to succeed without crashing, while unexpected service failures should still return an HTTP 500 response. Without tests for these cases, future changes could unintentionally alter this behavior without being detected.

---

## Map

Files involved:

- `api/routes/reviews.py`
- `core/services/review_service.py`
- `tests/unit/test_review_routes.py`

---

## Plan

1. Trace the `POST /reviews` request flow through `api/routes/reviews.py` and `core/services/review_service.py`.
2. Add a route-level unit test confirming that a documentless profile receives a pending review.
3. Add a test confirming that `process_review` is scheduled as a background task.
4. Add a test confirming that unexpected review-service failures return HTTP 500 and do not schedule background processing.
5. Run the targeted pytest suite, Ruff, Black, `make check`, and `make test-unit`, documenting unrelated pre-existing failures.

---

## Inputs & outputs

**Input**

- A request to create a review for a profile.
- A profile that has no ingested documents.

**Expected output**

- The endpoint returns a pending review response for a profile with no ingested documents.
- Background review processing is scheduled.
- Unexpected service failures return HTTP 500.
- Automated tests preserve these behaviors against regressions.
---

## Risks & unknowns

- Mocked route tests must still verify the correct service arguments and background-task behavior.
- The test response object must contain all fields required by `ReviewResponse`.
- Project-wide linting, type-checking, and unit-test failures may occur in unrelated files, so targeted checks must confirm that this contribution introduces no new failures.

---

## Edge cases

- A profile exists but has no resume, GitHub username, or portfolio URL.
- A pending review is returned with `sections=None` and `overall_score=None`.
- Exactly one background processing task is scheduled with the correct IDs.
- An unexpected service exception returns HTTP 500.
- No background task is scheduled when review creation fails.