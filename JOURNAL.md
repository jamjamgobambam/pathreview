## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue is about a missing test fixture file at `tests/fixtures/sample_profiles/basic_profile.json`. Several integration tests expect that sample profile to exist, but the fixture was deleted, so those tests cannot run normally and are being skipped. A successful fix would restore the JSON fixture with realistic sample portfolio data, including a GitHub username, resume information, and two repositories. This should make the affected integration tests usable again without changing the test logic itself.

**"Is this issue right for me?" checklist reasoning:**
I can explain this issue in my own words: the tests need a shared sample user profile fixture, but the expected JSON file is missing. The affected part of the codebase is limited to the test fixtures area, specifically `tests/fixtures/sample_profiles/basic_profile.json`, so the scope is clear and easy to locate. This is a good Tier 1 issue for me because it is self-contained, should only require restoring one realistic fixture file, and does not require changing the main app architecture. I understand what "done" looks like: the missing fixture should exist again with realistic sample data so the skipped integration tests can run. The estimated effort is 1–2 hours, and I do not see any blockers or dependencies listed on the issue.

**Branch name:** fix/106-user-prof-test-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
