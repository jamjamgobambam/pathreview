## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Several test and evaluation flows expect a sample profile at `tests/fixtures/sample_profiles/basic_profile.json`, but that fixture is missing from the repository. Without it, tests that need a realistic portfolio cannot run against consistent input and may be skipped or fail before exercising the application behavior. The change is limited to restoring well-formed test data containing a GitHub username, resume information, and two repositories. A successful fix will give the test suite a stable, reusable profile that matches the project's expected data shape.

**Branch name:** `test/106-restore-sample-profile-fixture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — “Is this issue right for me?” checklist

- **Understanding:** I can explain the missing behavior and define “done” as adding a valid, realistic JSON fixture that can be reused by the affected test and evaluation flows.
- **Tier fit:** I chose a Tier 1 issue because this is my first contribution to this large codebase. The work is localized to one new fixture file, does not require an architectural change, and the issue estimates only 1–2 hours of implementation work.
- **Codebase readiness:** I confirmed that the target fixture is absent, found the reference to sample profiles in `scripts/run_evals.py`, reviewed the profile fields in `api/schemas/profile.py`, and read the existing fixture and test patterns in `tests/conftest.py` and `tests/unit/test_review_service.py`.
- **Scope and time:** I checked the issue comments and the cohort ledger's claim count. Claims are non-exclusive, the issue has no listed blockers or unresolved dependencies, and the small file scope is realistic to complete and test before the Week 9 deadline.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Rithinteja/pathreview/commit/80325449f07e0955296ea4773fb816ec3cfc5cd3

**Reproduction summary:** I reproduced the missing-fixture gap from the repository root by checking `tests/fixtures/sample_profiles/basic_profile.json` and attempting to read it with `pathlib.Path.read_text()`. The path reported `exists=False`, and the read failed with `FileNotFoundError`, confirming that the benchmark profile referenced by `scripts/run_evals.py` is not available locally.

**PLAN.md link:** https://github.com/Rithinteja/pathreview/blob/test/106-restore-sample-profile-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded (recommended, not graded).

**Blockers or open questions:** `scripts/run_evals.py` currently contains only a TODO for loading benchmark profiles, so the exact JSON contract is not yet enforced in code. I will use the issue requirements and the existing profile model as the starting point, then make the fixture structure explicit in a focused validation test.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** I completed the first three implementation tasks from `PLAN.md`: defined the fixture contract, created `tests/fixtures/sample_profiles/basic_profile.json` with a fictional resume and two repositories, and added `tests/unit/test_basic_profile_fixture.py`. The focused test loads the JSON from a path anchored to the test file and verifies the required fields, nonblank content, repository count, and unique repository names.

**Next steps:** Run the JSON parser, focused test, `make test-unit`, and `make check`; compare the full-suite results with the pre-change baseline; then push the implementation and open a ready-for-review pull request with manual verification steps.

**Blockers:** The benchmark loader in `scripts/run_evals.py` is still a TODO, so it does not define an authoritative JSON schema. I addressed that uncertainty by documenting a minimal contract in the focused test and calling out the field-shape decision for reviewers instead of expanding the issue into evaluation-runner work.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/858

**Branch:** `test/106-restore-sample-profile-fixture`

**What you built:** I restored the missing shared sample portfolio with a fictional GitHub username, a populated resume, and exactly two realistic repositories. I also added a focused unit test that loads the fixture independently of the working directory and rejects missing, malformed, incomplete, blank, or duplicate repository data.

**Tests added or updated:** Added `tests/unit/test_basic_profile_fixture.py`. Its `test_basic_profile_fixture_has_expected_shape` test covers JSON loading, the required `github_username` and resume fields, exactly two repositories, nonblank repository metadata and README content, and unique repository names.

**Self-review confirmation:**

- [x] `make check` passes under the course's pre-existing-failure rule: the repository reports the same 182 existing Ruff findings before and after the change, while the new test file passes Ruff, Black, and the commit's mypy hook.
- [x] `make test-unit` passes under the course's pre-existing-failure rule: the same 53 existing tests fail before and after the change, and the passing count increases from 375 to 376 because the new test passes.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:** No reviewer or maintainer feedback has arrived on PR #858. This matches the Summer 2026 course note that reviewer feedback is not being provided, so there were no requested changes to document.

**How you responded:** No review response or follow-up code changes were needed. I left the pull request open and ready for review with the fixture schema decision and manual verification steps clearly documented for any future reviewer.

---

### Reflection

**What was harder than you expected?** Defining the JSON shape was harder than simply creating the missing file because `scripts/run_evals.py` only contains a TODO and does not specify a contract. I compared the issue requirements with `core/models/profile.py`, `api/schemas/profile.py`, and the existing fixtures in `tests/conftest.py`, then chose a small nested structure and documented that decision in `test_basic_profile_fixture_has_expected_shape`.

**What did you learn about working in a large codebase?** I learned that the source of truth can be spread across an issue, models, schemas, tests, and unfinished scripts instead of living in one place. Tracing those references before editing helped me keep issue #106 limited to `tests/fixtures/sample_profiles/basic_profile.json` and its validation test instead of expanding the work into implementing the entire evaluation runner.

**How did AI tools help — and where did they fall short?** AI tools helped me locate relevant files, compare the profile fields, organize the risks in `PLAN.md`, and turn the fixture requirements into concrete validation checks. They could not determine an authoritative schema that the repository itself does not define, and they could not replace running the project commands, so I still had to reproduce the `FileNotFoundError`, inspect the actual code, and compare the 53 unit-test failures and 182 lint findings before and after my change.

**What would you do differently if you started over?** I would run the full `make test-unit` and `make check` baseline at the start of Week 7 instead of waiting until implementation, because that would make the repository's pre-existing failures less surprising. I would also open the pull request earlier in Week 9 so the schema choice for the `resume` and `repositories` fields had more time to receive feedback.

**What are you most proud of from this module?** I am most proud that I turned a vague missing-fixture issue into a deterministic sample portfolio and a focused test that checks meaningful edge cases without depending on exact sample wording. I also documented the unchanged test and lint baselines clearly in JOURNAL.md and PR #858, which makes the contribution easier for another developer to evaluate.
