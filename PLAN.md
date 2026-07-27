# Solution plan

**Issue:** POST /reviews endpoint has no test for when the profile has no ingested documents ([#88](https://github.com/ascherj/pathreview/issues/88))

### Understand

This isn't actually a crash bug. It's a missing validation gap. `create_review_endpoint` in api/routes/reviews.py and `create_review` in core/services/review_service.py never check whether a profile has any ingested content, or even whether the profile exists, before creating a Review row and kicking off the background processing task. Expected behavior is that a profile with no github_username, portfolio_url, or resume_text (and therefore no IngestedSource rows) should get a clear error back. Actual behavior is the endpoint always returns 200 with status "pending," and the background process_review task later marks it "complete" using hardcoded placeholder feedback sections that ignore whether any real content was ever ingested. I confirmed this with a reproduction test in tests/unit/test_review_routes.py that currently fails, since it expects a 422 and gets a 200 instead.

### Map

- api/routes/reviews.py, create_review_endpoint. This is where the validation needs to get added before the review gets scheduled.
- core/services/review_service.py, create_review and _run_ingestion_pipeline. create_review is where the profile and its ingested content should get checked. _run_ingestion_pipeline is where the empty case is currently silently swallowed.
- core/models/ingested_source.py and core/models/profile.py. These define what "has content" actually means right now: github_username, portfolio_url, resume_text on Profile, or rows in IngestedSource.
- tests/unit/test_review_routes.py. This has the reproduction test and will need updating once the fix is in, plus a new regression test for the happy path.
- api/schemas/review.py. Review already has an error_message field, so the response shape probably doesn't need to change much.

### Plan

1. Add a lookup in create_review (or right in the endpoint) that checks the profile exists and has at least one of github_username, portfolio_url, resume_text set, or has IngestedSource rows.
2. If the profile doesn't exist or doesn't belong to the current user, return 404. If it exists but has no ingested content, return 422 with a clear detail message explaining why.
3. Leave process_review defensive too, so if it ever gets called directly outside the endpoint it still fails safely instead of completing with fake content.
4. Update the reproduction test in tests/unit/test_review_routes.py so it asserts the new passing behavior, and add a second test confirming a profile that does have content still returns 200 with status "pending" like before.
5. Check frontend/src/pages/ReviewPage.tsx and frontend/src/hooks/useReviewStatus.ts to see if they assume review creation always succeeds, and update them to handle the new error response if needed.

### Inputs & outputs

Input stays the same, just profile_id on POST /reviews. What changes is the output: a profile with no ingested content now gets a 422 with an explanation instead of a silent 200. A missing or not-owned profile now gets a 404 instead of being allowed through. The happy path response shape doesn't change at all.

### Risks & unknowns

I'm still not sure whether "has content" should be based on the three profile fields directly or on actually counting IngestedSource rows for that profile. Right now they're equivalent since _run_ingestion_pipeline is the only thing that ever creates IngestedSource rows, but ingestion/pipeline.py has placeholder logic hinting at a bigger real ingestion pipeline down the line, so checking IngestedSource directly is probably more future proof. I also don't know if the frontend assumes POST /reviews always succeeds, that needs a quick look before shipping this. And there's no existing DB backed integration test pattern in this repo, everything so far is mocked sessions, so a more realistic end to end test isn't something I can model off an existing example yet.

### Edge cases

- Profile ID doesn't exist at all, should be 404.
- Profile has resume_filename set but resume_text is empty or null, that's a partial upload and probably still counts as no content.
- A future ingestion path creates IngestedSource rows without ever touching the three profile text fields, the check should hold up against that by counting IngestedSource rows instead of only checking the profile fields.
- Someone uploads content to their profile while a review request for that same profile is already in flight, this is a race condition I'm noting but not planning to handle in this fix.
