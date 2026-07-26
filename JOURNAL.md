## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The project has no `tests/fixtures/` directory, so any test that needs a sample user profile (with fields like `github_username`, `resume_text`, and `portfolio_url`) must construct its own inline object. This duplication means the fixture data can drift across test files — one test might use a different set of fields than another — making it harder to keep tests consistent and maintainable. The fix is to create a `tests/fixtures/` directory and add a shared `sample_profile` fixture (likely in `conftest.py` or a dedicated fixtures module) that every unit and integration test can import. A successful resolution means tests across the suite reference a single source of truth for profile data, reducing boilerplate and making future schema changes easier to apply uniformly.

**Branch name:** test/106-shared-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tracira/pathreview/commit/b14719b

**Reproduction summary:**
Added `tests/integration/test_shared_profile_fixture.py` which tries to open `tests/fixtures/sample_profiles/basic_profile.json`. Running `pytest` confirms the issue: 1 test fails with `AssertionError: Missing fixture file` and 2 downstream tests skip, because neither the `tests/fixtures/` directory nor the JSON file exists anywhere in the repo.

**PLAN.md link:** https://github.com/tracira/pathreview/blob/test/106-shared-profile-fixture/PLAN.md

**Walkthrough video (recommended):** <!-- add Loom link here -->

**Blockers or open questions:**
The `repos` field in the planned fixture JSON has no corresponding column in the `Profile` ORM model — repos live in `IngestedSource`. Need to decide whether the fixture should include `repos` purely as supplemental test data (a plain dict field) or whether the fixture should omit it and let individual tests supply repo data separately.
