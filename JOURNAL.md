## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The project has no `tests/fixtures/` directory, so any test that needs a sample user profile (with fields like `github_username`, `resume_text`, and `portfolio_url`) must construct its own inline object. This duplication means the fixture data can drift across test files — one test might use a different set of fields than another — making it harder to keep tests consistent and maintainable. The fix is to create a `tests/fixtures/` directory and add a shared `sample_profile` fixture (likely in `conftest.py` or a dedicated fixtures module) that every unit and integration test can import. A successful resolution means tests across the suite reference a single source of truth for profile data, reducing boilerplate and making future schema changes easier to apply uniformly.

**Branch name:** test/106-shared-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tracira/pathreview/commit/b14719b

**Reproduction summary:**
Added `tests/integration/test_shared_profile_fixture.py` which tries to open `tests/fixtures/sample_profiles/basic_profile.json`. Running `pytest` confirms the issue: 1 test fails with `AssertionError: Missing fixture file` and 2 downstream tests skip, because neither the `tests/fixtures/` directory nor the JSON file exists anywhere in the repo.

**PLAN.md link:** https://github.com/tracira/pathreview/blob/test/106-shared-profile-fixture/PLAN.md

**Walkthrough video (recommended):** <!-- add Loom link here -->

**Blockers or open questions:**
The `repos` field in the planned fixture JSON has no corresponding column in the `Profile` ORM model — repos live in `IngestedSource`. Need to decide whether the fixture should include `repos` purely as supplemental test data (a plain dict field) or whether the fixture should omit it and let individual tests supply repo data separately.

## Week 9 — Mid-week check-in

**What's done:**
- Created `tests/fixtures/sample_profiles/basic_profile.json` with realistic data covering all nullable Profile model fields (`github_username`, `resume_filename`, `resume_text`, `portfolio_url`) plus a supplemental `repos` array with two sample repositories. Stored UUIDs as strings to match `UUID(as_uuid=False)` column config.
- Added a `sample_profile` fixture to `tests/conftest.py` that loads and returns the JSON dict. Any test can request it by name without duplicating the data.
- Removed the now-redundant local `mock_profile` fixture from `tests/unit/test_review_service.py`.
- All three reproduction tests in `tests/integration/test_shared_profile_fixture.py` pass (was 1 fail + 2 skip before the fix).
- Ran the full unit suite to check for regressions — the 13 pre-existing failures in `test_review_service.py` are caused by an unrelated `AsyncMock.scalars()` mock setup bug and were already failing on this branch before my changes.

**Decision made on the `repos` blocker:** included `repos` in the fixture JSON as supplemental test data only; the `conftest.py` docstring makes clear it is not a direct DB mapping. Tests that need real `IngestedSource` rows should construct those separately.

**What's left:** submit the pull request.

## Week 9 — Submission

**PR link:** <!-- add PR URL here after opening -->

**What the PR does:**
Adds the missing shared profile fixture described in issue #106. The change is self-contained: one new JSON file, one new pytest fixture in `conftest.py`, and one cleanup in `test_review_service.py`. No production code was touched.

**Testing:**
- `pytest tests/integration/test_shared_profile_fixture.py -v` → 3 passed, 0 failed
- Full unit suite shows no new failures introduced by this change

**Anything you'd do differently next time:**
I'd check earlier whether the `mock_profile` fixture in `test_review_service.py` was actually used by any test before planning to migrate it — it turned out to be completely unused, so the "migration" was just a deletion.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. The Summer 2026 cohort does not include maintainer feedback as a feature — noted per course instructions.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Understanding the existing test infrastructure took longer than expected. Before writing a single line of fixture code, I had to trace through how `conftest.py` worked, where pytest looked for fixtures, and why the pre-existing failures in `test_review_service.py` were showing up even on a branch that hadn't touched those files. Separating "failures my change caused" from "failures that were already there" required running the suite on the base branch and diffing the results — something I hadn't planned time for.

**What did you learn about working in a large codebase?**
The surface area of a change is never just the files you edit. Adding a shared fixture in `conftest.py` immediately raised questions about the ORM model (`Profile`), the `IngestedSource` table, UUID column configuration, and what "realistic" test data even looks like for this domain. In my own projects I just make up data on the fly; here, getting the fixture wrong would silently break tests in ways that are hard to trace. Working in someone else's codebase means you have to earn the right to make assumptions, and that takes research time you don't initially budget for.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigating unfamiliar code quickly — explaining what `UUID(as_uuid=False)` means in SQLAlchemy context, helping me draft the `conftest.py` docstring, and sanity-checking whether the fixture structure I planned would work with pytest's fixture scoping rules. Where it fell short: the AI couldn't tell me whether pre-existing test failures were intentional (known-broken tests the team was ignoring) or accidental (tests that broke with a recent refactor). That required reading the git history and making a judgment call. AI gives you speed; it doesn't give you project context.

**What would you do differently if you started over?**
I'd read the open issues list more carefully before selecting one. Issue #106 was well-scoped and achievable, which was the right call for a first open-source contribution, but I spent time in Week 8 worrying about the `repos` field blocker that I could have resolved in 20 minutes with a clearer read of the ORM schema upfront. Better pre-work on the data model would have let me write a cleaner PLAN.md with fewer open questions.

**What are you most proud of from this module?**
The decision to keep `repos` in the fixture JSON as explicit supplemental data rather than either dropping it or trying to make it map to a DB column. That choice required understanding the difference between "test data" and "DB-backed data," documenting it clearly in the `conftest.py` docstring, and accepting that the fixture wouldn't be a perfect mirror of the ORM model. It was a small architectural judgment call in a small PR, but it felt like thinking like a contributor rather than just following the issue description literally.
