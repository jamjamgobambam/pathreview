## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/88)]

**Issue title:** [POST /reviews endpoint has no test for when the profile has no ingested documents
]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint lets a user request an AI review of a profile, but
there is no test covering the case where the profile exists yet has no ingested
content (i.e. the profile has no content to review). What's missing is
purely test coverage for this edge case in `tests/unit/test_review_routes.py` —
a file that doesn't exist yet. This matters because the endpoint currently
doesn't validate that a profile has any content before starting a review:
instead of returning a clear client error, it silently accepts the request and
the background pipeline goes on to produce a review anyway. A successful fix adds
a test that drives the endpoint with a content-less profile and asserts it
responds with an appropriate error (a 4xx) rather than crashing or silently
"succeeding," which pins down the intended behavior for this edge case. This
affects the review API route (`api/routes/reviews.py`) and its processing logic
in `core/services/review_service.py`.

**Branch name:** [test/88-verify-review-endpoint-tests]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger