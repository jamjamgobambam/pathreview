## Week 7 — Issue selection


**Issue link:** https://github.com/ascherj/pathreview/issues/88


**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3


**Problem summary:**
From reading the issue, it looks like `POST /reviews` is missing a test for the scenario where a profile exists but no resume or repositories have been ingested yet. Since the review generator wouldn't have any data to work with, I'll verify how the endpoint currently handles that situation and add a test in `tests/unit/test_review_routes.py` to ensure it returns an appropriate error rather than crashing.


**Branch name:** test/88-review-endpoint-no-ingested-content


**Setup confirmation:** [x] App runs locally at localhost:5173


**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jupitersnow1/pathreview/commit/4323e66 

**Reproduction summary:**
I called the review pipeline directly with a mock profile that had no GitHub, portfolio, or resume data and confirmed the ingestion step returned an empty source list. Even with no sources to process, the downstream generation steps still produced the same hardcoded feedback, and the review completed successfully instead of reporting an error.

**PLAN.md link:** https://github.com/jupitersnow1/pathreview/blob/test/88-review-endpoint-no-ingested-content/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
I'm still deciding where the validation should happen. One option is to check in the create_review endpoint so the request fails immediately before a review record is created. The other option is to let the review be created and have process_review detect the missing data, mark the review as status="failed", and include a clear error message.

Right now I'm leaning toward validating in the endpoint because it prevents creating a misleading pending review in the first place. I just want to make sure that's the approach the frontend is expecting when a submission doesn't include enough information to generate a review.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix outlined in PLAN.md by adding check_has_ingested_sources in core/services/review_service.py and calling it from create_review_endpoint in api/routes/reviews.py. Now, if a profile has no ingested sources, the endpoint returns a 400 Bad Request with the message "Profile has no ingested content" before creating a review or scheduling process_review.

I also added unit tests in tests/unit/test_review_routes.py to cover both scenarios: rejecting requests when there are no ingested sources and confirming the normal review creation flow still works when ingested content exists.

Steps 1–4 from PLAN.md are complete. I looked into the stretch service-layer test, but decided it wasn't needed because the new guard prevents process_review from being scheduled in the first place, so the downstream orchestration code is no longer reachable.

**Next steps:**
Run make check and make test-unit, compare any failures against the existing baseline, split the work into focused commits, and open a draft PR for feedback before submitting the final version.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** test/88-review-endpoint-no-ingested-content

**What you built:**
Added a guard to POST /reviews that returns a 400 Bad Request when the target profile has no IngestedSource records, preventing the endpoint from creating a review with placeholder feedback.

**Tests added or updated:**
`tests/unit/test_review_routes.py` (new) — tests the 400-rejection path and the happy-path pending-review creation for `create_review_endpoint`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
