## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/88)]

**Issue title:** [POST /reviews endpoint has no test for when the profile has no ingested documents
]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint (in `api/routes/reviews.py`, with logic in
`core/services/review_service.py`) lets a user request an AI review of a profile,
but there is no test for the case where the profile exists yet has no content to
review. Currently the endpoint doesn't validate this — instead of returning a
clear client error, it silently accepts the request and the background pipeline
produces a review anyway, so a successful fix adds a test in the not-yet-created
`tests/unit/test_review_routes.py` that drives the endpoint with a content-less
profile and asserts it responds with an appropriate 4xx error rather than
crashing or silently succeeding. This is a good Tier 1 fit for me: the change is
localized to a single test file and doesn't require understanding the whole
system, and I've confirmed the referenced files exist. I've read the specific
code (`create_review_endpoint` → `process_review` → `_run_ingestion_pipeline`)
and the existing `tests/unit/test_review_service.py` end-to-end for its
fixture/mock/assertion patterns, so I can plan the fix (FastAPI TestClient +
`dependency_overrides` to fake auth and the DB). The manifest estimates 2–3
hours with no blockers, and although the ledger shows 3 others have claimed it,
claims are non-exclusive so I'm comfortable proceeding.

**Branch name:** [test/88-verify-review-endpoint-tests]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger