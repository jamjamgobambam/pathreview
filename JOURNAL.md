# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint (in `api/routes/reviews.py`) lets a user kick off a
review for one of their profiles. It creates a review row with `status="pending"`,
returns immediately, and does the heavy lifting in a background task (`process_review` in `core/services/review_service.py`). One realistic situation is a profile that has no ingested documents at all i.e. no GitHub username, portfolio URL, or uploaded resume. This makes the ingestion step produce an empty result set. Right now nothing pins down how the endpoint should behave in that case: the only review tests live in `tests/unit/test_review_service.py`, and there is no test for the empty-profile path, so a future change could silently break it. A successful fix adds a focused test that submits a review for a profile with zero ingested documents and asserts the endpoint's contract (that it still responds as designed rather than erroring on empty input), closing the coverage gap.

**Branch name:** test/88-reviews-no-ingested-docs

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" checklist reasoning:**
This fits my scope as a first contribution for a few reasons. It is test-only work in which I add a test rather than change product behavior, so the blast radius is small and I am unlikely to break existing features. I was able to locate the relevant code
quickly: the handler in `api/routes/reviews.py`, the background logic in
`core/services/review_service.py`, and the existing tests in
`tests/unit/test_review_service.py`, which gives me a pattern to follow. I understand
what "no ingested documents" means in the data model (a profile with no GitHub
username, portfolio URL, or resume, so no `IngestedSource` rows), which is the exact
condition the new test needs to set up. The main thing I need to confirm is the
endpoint's intended behavior in that case so my assertion matches the design rather
than the current implementation.