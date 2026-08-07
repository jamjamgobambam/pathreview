## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All three sub-tasks from PLAN.md are complete:
- ✅ Sub-task 1 — Recreated `tests/fixtures/sample_profiles/` directory and `basic_profile.json` with a realistic two-repo portfolio (GitHub username, full resume text, two project entries each containing `github_repo`, `name`, `description`, and `readme_content`).
- ✅ Sub-task 2 — Wrote `tests/integration/test_sample_profile_fixture.py` (11 tests across three classes: structure validation, per-repository field checks, and Orchestrator compatibility). Tests skipped before the fixture was present, confirming the silent-skip behaviour in issue #106; all 11 pass after the fixture was restored.
- ✅ Sub-task 3 — Verified fixture schema against `Orchestrator._build_plan` — `github_username`, `resume_text`, and `projects[*].github_repo` are all present so the orchestrator queues the expected tools.

**Next steps:**
Run final pre-submission checks (`make check`, `make test-unit`), document pre-existing failures, and open the pull request.

**Blockers:**
None. Pre-existing `make check` and `make test-unit` failures exist in the codebase but are unrelated to this fix (see Check-in 2 for details).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/271

**Branch:** `fix/106-restore-basic-profile-fixture`

**What you built:**
Restored the deleted `tests/fixtures/sample_profiles/basic_profile.json` with a realistic two-repository sample portfolio (GitHub username, resume text, and two project entries), and wrote 11 integration tests in `tests/integration/test_sample_profile_fixture.py` that validate the fixture's structure and confirm it is compatible with `Orchestrator._build_plan`. Before the fixture was present all 11 tests silently skipped, exactly reproducing issue #106; after the restore all 11 pass.

**Tests added or updated:**
- **`tests/integration/test_sample_profile_fixture.py`** (new, 11 tests):
  - `TestBasicProfileFixtureStructure` — asserts the JSON loads, has a non-blank `github_username`, a non-empty `resume_text`, a `projects` list, and exactly two repositories.
  - `TestBasicProfileRepositoryFields` — asserts every project entry has `github_repo`, `name`, `description`, and `readme_content`; asserts the two repo names are distinct.
  - `TestBasicProfileOrchestratorCompatibility` — calls `Orchestrator._build_plan` directly with the fixture data and asserts it returns a list containing a `skill_extractor` step (confirming the fixture feeds the pipeline correctly).

**Self-review confirmation:**
- [x] `make check` passes for files touched by this PR (pre-existing lint/type errors in unrelated files are documented in Notes for Reviewers)
- [x] `make test-unit` — our 11 integration tests pass; pre-existing unit-test failures in unrelated files are documented in Notes for Reviewers

**Draft PR feedback received from:** *(none)*

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Azu06FTW/pathreview/commit/cc3f6a7

**Reproduction summary:**
Created `tests/integration/test_sample_profile_fixture.py`, which uses
`pytest.mark.skipif` to skip all 11 integration tests when
`tests/fixtures/sample_profiles/basic_profile.json` is absent. Running
`pytest tests/integration/test_sample_profile_fixture.py -v` before the
fixture was restored showed **11 skipped** — confirming the silent-skip
behaviour described in issue #106.

**PLAN.md link:** https://github.com/Azu06FTW/pathreview/blob/fix/106-restore-basic-profile-fixture/PLAN.md

**Walkthrough video (recommended):** *(not recorded)*

**Blockers or open questions:**
- `scripts/run_evals.py` loads benchmark portfolios from this directory but
  the load logic is a `TODO`. The fixture schema was derived from
  `Orchestrator._build_plan`; if the eval runner is later implemented with a
  different schema, the fixture may need updating.

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
A JSON fixture file at `tests/fixtures/sample_profiles/basic_profile.json` was deleted from the repository. Multiple integration tests depend on this file to run, and without it they silently skip instead of executing. The file is supposed to contain a realistic sample portfolio — a GitHub username, a resume, and data for two repositories. The fix is to recreate the missing directory and file with valid sample data so the skipped tests can run again. No logic changes are needed anywhere else in the codebase.

**Branch name:** fix/106-restore-basic-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
