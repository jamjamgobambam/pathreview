# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [] Tier 3

**Problem summary:**
`docs/API.md` lists the response shape for every endpoint but never documents what a client actually needs to send when creating a profile or requesting a review. This is confusing in practice because `POST /profiles` isn't a plain JSON request — it's `multipart/form-data`, since it accepts an optional resume file upload alongside `github_username` and `portfolio_url` fields, and that distinction wasn't documented anywhere. `POST /reviews` is simpler (JSON with just a `profile_id`), but it also had no documented request format. A successful fix adds field-level tables and example requests for both endpoints so a new API consumer doesn't have to read `api/routes/profiles.py` and `api/schemas/review.py` just to figure out how to call them.

**Branch name:** docs/89-post-profiles-schema

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger