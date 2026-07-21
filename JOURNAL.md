## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The project has no `tests/fixtures/` directory, so any test that needs a sample user profile (with fields like `github_username`, `resume_text`, and `portfolio_url`) must construct its own inline object. This duplication means the fixture data can drift across test files — one test might use a different set of fields than another — making it harder to keep tests consistent and maintainable. The fix is to create a `tests/fixtures/` directory and add a shared `sample_profile` fixture (likely in `conftest.py` or a dedicated fixtures module) that every unit and integration test can import. A successful resolution means tests across the suite reference a single source of truth for profile data, reducing boilerplate and making future schema changes easier to apply uniformly.

**Branch name:** test/106-shared-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
