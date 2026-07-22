# PathReview Development Journal

This journal tracks progress and reflections weekly throughout Module 3.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from tests/fixtures/

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, several integration tests in the test suite are failing or being skipped because a critical JSON test fixture (`tests/fixtures/sample_profiles/basic_profile.json`) was deleted. This issue affects the testing environment, specifically the `tests/fixtures/` directory. A successful fix will restore a realistic sample user profile containing a GitHub username, a resume, and two repositories, thereby stabilizing the integration tests and ensuring they run reliably during CI/CD.

### "Is this right for me?" checklist & reasoning
- [x] **Clear Scope:** The issue clearly outlines the missing test fixture `tests/fixtures/sample_profiles/basic_profile.json` that needs to be recreated.
- [x] **Testable:** Verify the fix by running the integration tests that depend on this fixture.
- [x] **Manageable Size:** A JSON file containing a realistic user profile (GitHub username, resume, and two repos) is a concise task that doesn't involve complex logic, making it manageable.
- [x] **No Core Blockers:** It is isolated to `tests/fixtures/` and does not require modifying critical business logic or third-party APIs.
- **Scope Reasoning:** This Tier 1 issue is ideal for me to learn the repository's structure and contribution workflow. Restoring the deleted test fixture is high-value for project health since it fixes broken/skipped integration tests, yet it remains low-risk and well-defined.

**Branch name:** chore/106-setup-env

**Setup confirmation:** [x] App runs locally.

**Cohort ledger:** [x] Issue added to cohort ledger

**Reproduction summary:**
I verified the issue by implementing a dedicated unit test at `tests/unit/test_fixtures.py` that asserts the existence and verifies the schema structure of `tests/fixtures/sample_profiles/basic_profile.json`.

**Bug Reproduction:**
   When the fixture is missing, running the test with `.venv/Scripts/pytest tests/unit/test_fixtures.py` reliably reproduces failure.
