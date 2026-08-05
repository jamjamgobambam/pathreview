## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106
**Issue title:** Restore deleted basic_profile.json fixture
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Multiple integration tests in the test suite are currently skipped because a required test fixture file, `tests/fixtures/sample_profiles/basic_profile.json`, was deleted from the repository. Without this file, integration tests that depend on a baseline user profile cannot execute properly. Restoring this fixture with a realistic sample portfolio containing a GitHub username, resume text, and two repository links will allow those skipped integration tests to run cleanly and pass.

**Branch name:** fix/106-restore-basic-profile-fixture
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [placeholder for commit link]

**Reproduction summary:**
I reproduced the issue by confirming the file `tests/fixtures/sample_profiles/basic_profile.json` was missing from the repository. I observed that while no tests failed (because the tests themselves are also missing), the issue description `G-01` and the project structure clearly indicate this file is a required test fixture.

**PLAN.md link:** [placeholder for PLAN.md link]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
The integration tests that are supposed to use this fixture are not present in the repository. While restoring the fixture is the correct fix for this issue, the ultimate validation would require finding or rewriting those tests.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Restored `tests/fixtures/sample_profiles/basic_profile.json` and enriched it into a realistic portfolio: a GitHub username, a resume with recognizable sections, and two differentiated repositories (a Python repo with tests + CI, and a TypeScript repo without) shaped with the GitHub-API fields that `RepoAnalyzer` actually reads. Wrote `tests/unit/test_basic_profile_fixture.py` (5 tests) that loads the fixture and feeds it through the real `ResumeParser` and `RepoAnalyzer`, asserting the expected sections and repo signals. All 5 pass; the new file is `ruff`/`black`/`mypy` clean.

**Next steps:**
Open the PR, request peer feedback, and finalize the submission.

**Blockers:**
None. Noted pre-existing, unrelated failures in the codebase (see Check-in 2) that my change does not affect.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ChristopherPaladines/pathreview/pull/1

**Branch:** `fix/106-restore-basic-profile-fixture`

**What you built:**
Restored the deleted `basic_profile.json` fixture with a realistic sample portfolio and added a unit test that loads it and runs it through the real `ResumeParser` and `RepoAnalyzer`, verifying the fixture is valid/usable and guarding it against future deletion.

**Tests added or updated:**
Added `tests/unit/test_basic_profile_fixture.py` (5 tests): fixture loads, required top-level keys present, resume text parses into detected sections, and each repository is analyzed with the expected language / tests / CI signals.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Codebase has documented pre-existing failures — baseline `make test-unit`: 53 failed / 375 passed; `make lint`: 182 errors. After my change: 53 failed / 380 passed = +5 passing, 0 new failures. My new file passes ruff/black/mypy. Per the Week 9 guidance, "passes" here means my change introduces no new failures.)

**Draft PR feedback received from:** none
