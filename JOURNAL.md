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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [ed63377](https://github.com/shp5238/pathreview/commit/ed633772c80709424fa7f5365589ff49be1e7f61)

**Reproduction summary:**
I reproduced the issue by checking for `tests/fixtures/sample_profiles/basic_profile.json` and confirming that the expected fixture path does not exist in the repository. The issue is that manifest and eval tooling still reference `tests/fixtures/sample_profiles/`, so tests or scripts that depend on this shared sample profile cannot run against the expected fixture data.


**PLAN.md link:** [./PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded](loom video demo link)

**Blockers or open questions:**
Need to confirm the exact JSON shape expected by the skipped integration tests before writing the fixture. If those tests are not currently present or are also skipped/unfinished, I will model the fixture around the existing profile, resume, repository, and ingestion schemas so it remains realistic and reusable.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed sub-tasks from PLAN.md: (1) searched the suite for references to `basic_profile.json` / `sample_profiles`, (2) derived the expected JSON shape from `api/schemas/profile.py`, `core/models/profile.py`, and the ingestion parsers, and (3) restored the missing fixture at `tests/fixtures/sample_profiles/basic_profile.json` with realistic fake data (github_username, resume text, two repositories) plus a test that asserts its structure.

Validation:
- .venv/bin/pytest tests/integration/test_sample_profile_fixture.py -v: passes, 2 passed
- make test-unit: fails with 53 existing unit test failures across unrelated modules; this fixture-only change does not modify those modules
- make check: fails during ruff linting with 182 existing lint errors across unrelated files; this change introduces 0 new lint errors

**Next steps:**
Run `make check` and `make test-unit` to confirm no new failures, finalize the PR description, and open the PR for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/968

**Branch:** `fix/106-user-prof-test-fixture`

**What you built:**
I restored the missing sample profile fixture used by integration tests. The fixture contains realistic fake portfolio data, including a GitHub username, resume content, and two repository entries.

**Tests added or updated:**
Added `tests/integration/test_sample_profile_fixture.py` covering that the restored fixture `tests/fixtures/sample_profiles/basic_profile.json` exists, parses as a JSON object, carries the required top-level keys (`github_username`, `resume_filename`, `resume_text`), and contains exactly two repositories, each with the required keys (`html_url`, `readme_content`, `file_structure`).

**Self-review confirmation:** [X] make check passes [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback arrived on my PR during the review period. Because reviewer feedback is not provided for Summer 2026, I am documenting that outcome here and closing out the module based on my own validation and reflection.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was determining the exact shape of the missing `tests/fixtures/sample_profiles/basic_profile.json` fixture. The issue sounded like restoring a single file, but I needed to trace the expected fields through `api/schemas/profile.py`, `core/models/profile.py`, and the ingestion parsers before I could be confident that the fixture would be useful rather than just valid JSON. Writing `tests/integration/test_sample_profile_fixture.py` also made me think through which details should be protected by tests, such as the top-level profile keys and repository fields.

**What did you learn about working in a large codebase?**
I learned that even a small contribution has to fit conventions and dependencies that are spread across many files. In this repository, the missing fixture was referenced by tooling and tests, while the data it needed was defined by schemas and models elsewhere; changing only the obvious file would not have been enough. Working in someone else's codebase meant I had to first gather evidence about expected behavior instead of deciding the data format on my own.

**How did AI tools help — and where did they fall short?**
AI was useful for helping me search for references to `basic_profile.json` and `sample_profiles`, organize the investigation, and identify files that could define the expected profile structure. It was less useful as a source of truth: I still needed to inspect the actual schemas and parsers, choose realistic fake data, and run the targeted tests and project checks myself. The experience reinforced that AI can speed up exploration, but it cannot replace verification against the repository.

**What would you do differently if you started over?**
If I started over, I would begin by mapping every fixture reference and the exact test command earlier, before drafting the fixture content. That would make the planning stage more direct and reduce the need to revisit assumptions about required repository fields. I would also record the final validation results in one place sooner, so the journal's progress notes remain easier to reconcile as the work moves from investigation to submission.

**What are you most proud of from this module?**
I am most proud of turning a missing shared test asset into a regression-protected contribution rather than simply recreating a file. The restored `basic_profile.json` contains realistic fake portfolio data, and the integration test confirms both that it can be parsed and that its important structure remains available. That work leaves the test suite with a clearer, reusable fixture for future contributors.
