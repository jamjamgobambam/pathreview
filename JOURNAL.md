# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The review routes have basically no test coverage right now. The file the issue points to, tests/unit/test_review_routes.py, does not even exist in the repo. The closest thing we have is tests/unit/test_review_service.py, and that file only tests create_review, get_review, and list_reviews against a mocked DB session. It never spins up the actual POST /reviews endpoint and never touches process_review, which is the background task that actually runs the ingestion pipeline. So right now nothing proves what happens when someone creates a review for a profile that has no github username, portfolio url, or resume text on file. A fix here means adding a test that hits the endpoint with that kind of empty profile and confirms we get back a sane error instead of a crash or a silent pending review that never resolves.

**Branch name:** test/88-review-no-ingested-content

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
