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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/krish-batra/pathreview/commit/8b724fb78d4b4f2d9f169303cf70aa73799a756e

**Reproduction summary:** The issue could not be reproduced as literally
described — the fixture `tests/fixtures/sample_profiles/basic_profile.json`
never existed in git history (confirmed via `git log --all` and a full-history
`git grep`) and `tests/integration/` was empty, so no tests were actually being
skipped. This is a seeded/synthetic practice issue, so the work was net-new
authoring of the fixture plus a matching integration test, not restoration of a
deleted file.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:** None blocking. Note for reviewers: PR #134
attempted a different (conftest.py Python fixture) approach that never created
the JSON path the issue names and stalled unmerged; this branch delivers the
literal JSON fixture instead. The repo also has 53 pre-existing unit-test
failures unrelated to this change (all in `tests/unit/`); the 3 new integration
tests pass and the full suite is 378 passed / 53 failed.