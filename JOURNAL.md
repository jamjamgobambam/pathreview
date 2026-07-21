## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Several integration tests depend on a fixture file,
`tests/fixtures/sample_profiles/basic_profile.json`, that no longer exists
in the repository — it was deleted at some point, and the tests that
reference it are currently being skipped rather than run. This means test
coverage for whatever functionality relies on that fixture is effectively
absent right now. The fix is to recreate the fixture as a realistic sample
user profile containing a GitHub username, a resume, and two repositories,
matching whatever shape the skipped tests expect it to have. Once restored,
those integration tests should un-skip and run against real (if synthetic)
profile data, closing the coverage gap.

**Branch name:** fix/106-restore-sample-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger