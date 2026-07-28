## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Issue #106 addresses a missing shared test fixture: `tests/fixtures/sample_profiles/basic_profile.json`. The fixture was removed, causing tests that depend on reusable sample profile data to lack a consistent input containing GitHub information, resume details, and repository examples. I verified that the `tests/fixtures/` directory is missing and that `tests/conftest.py` currently only provides resume and README fixtures. The fix will restore a standard sample profile fixture so tests can use consistent data and avoid duplicated setup.

### Is This Issue Right for Me?

- **Understanding** — I verified the missing fixture issue by inspecting the test structure and confirmed that shared sample profile data needs to be restored.
- **Tier Fit** — This is a Tier 1 issue that matches my current experience because it is a focused test infrastructure change involving adding missing fixture data rather than modifying production behavior.
- **Scope** — Small and well-bounded: restore one shared sample profile fixture (`tests/fixtures/sample_profiles/basic_profile.json`). No production code changes are required.
- **Effort (Time)** — Reasonable for Weeks 8–9. The work involves creating realistic sample data, matching the expected profile structure, and running the test suite.
- **Dependencies** — None external. The fixture uses static test data and does not require database changes, API keys, or external services.
- **Verification** — I can validate the change by running `make test-unit` and confirming the related tests pass.

**Branch name:** `test/106-restore-basic-profile-fixture`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/michellejtan/pathreview/commit/7301bcdc4ebb6bb816b98b3c75319cabc849bd20

**Reproduction summary:**
Ran `ls tests/fixtures` and `find tests -iname "*profile*"` — confirmed the
`tests/fixtures/sample_profiles/basic_profile.json` file and its parent folder
do not exist anywhere in the repo, and no test currently imports it. The only
remaining reference is a TODO comment in `scripts/run_evals.py` pointing at
that path, suggesting the fixture was removed (or never committed) at some
point and the reference was left behind.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]