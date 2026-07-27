## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106
**Issue title:** Restore deleted basic_profile.json fixture
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Multiple integration tests in the test suite are currently skipped because a required test fixture file, `tests/fixtures/sample_profiles/basic_profile.json`, was deleted from the repository. Without this file, integration tests that depend on a baseline user profile cannot execute properly. Restoring this fixture with a realistic sample portfolio containing a GitHub username, resume text, and two repository links will allow those skipped integration tests to run cleanly and pass.

**Branch name:** fix/106-restore-basic-profile-fixture
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger
