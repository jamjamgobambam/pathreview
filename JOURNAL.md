# JOURNAL

## Week 7 Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists the response shape for every endpoint but never documents what a client actually needs to send when creating a profile or requesting a review. This is confusing in practice because `POST /profiles` isn't a plain JSON request â€” it's `multipart/form-data`, since it accepts an optional resume file upload alongside `github_username` and `portfolio_url` fields, and that distinction wasn't documented anywhere. `POST /reviews` is simpler (JSON with just a `profile_id`), but it also had no documented request format. A successful fix adds field-level tables and example requests for both endpoints so a new API consumer doesn't have to read `api/routes/profiles.py` and `api/schemas/review.py` just to figure out how to call them.

**Branch name:** docs/89-post-profiles-schema

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 Reproduction & solution planning

**Reproduction commit link:** https://github.com/RithikaMathew/pathreview/commit/60fa346

**Reproduction summary:**
Ran the app locally and compared the auto-generated OpenAPI schema at `localhost:8000/docs` against the pre-fix version of `docs/API.md` (commit 888af31). Confirmed `POST /profiles` is multipart form data with an optional resume file, and `POST /reviews` is JSON with just `profile_id` â€” neither was documented before this fix.

**PLAN.md link:** https://github.com/RithikaMathew/pathreview/blob/docs/89-post-profiles-schema/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**

