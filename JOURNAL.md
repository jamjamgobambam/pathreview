## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's test suite is meant to share a single canned user portfolio —
stored at `tests/fixtures/sample_profiles/basic_profile.json` — that
integration tests load to drive the ingestion and review pipeline end to end.
That fixture (in fact the entire `tests/fixtures/` directory) is currently
missing from the repo, so any test depending on it cannot run and is skipped,
leaving that pipeline path unverified. Fixing it means recreating the fixture
as a realistic sample portfolio: a GitHub username, resume text, and two
repositories described with the GitHub-API-style fields the ingestion parsers
already expect (`name`, `language`, `stargazers_count`, `html_url`,
`readme_content`, etc.). Once the file exists and matches those shapes, the
dependent integration tests can load real data and exercise the pipeline
instead of being skipped. The change is confined to test fixtures (and possibly
a small loader in `tests/conftest.py`) and touches no production code.

**Branch name:** test/106-restore-basic-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduce the issue and plan the fix

**Reproduction summary:**
Before reproducing, I checked the repo's actual state rather than trusting the
issue text: `git log --all --full-history -- tests/fixtures/**` returns zero
commits, meaning the fixture never existed in history, and `origin/main` is
identical to `upstream/main` (0 commits apart either way), so this isn't a
stale-fork issue. `tests/integration/` contained only an empty `__init__.py` —
no existing test depended on the fixture. To make the bug concrete and
verifiable, I added a `basic_profile` loader fixture to `tests/conftest.py`
and a new integration test, `tests/integration/test_sample_profile_fixture.py`,
that loads `tests/fixtures/sample_profiles/basic_profile.json` and feeds it
through `RepoAnalyzer` and `ResumeParser`. Running
`pytest tests/integration -m integration -v` fails all three tests with
`FileNotFoundError` at the fixture-load step, before any parser code runs —
confirming the root cause is simply that the fixture file is missing.

**Reproduction commit:** https://github.com/ujval9/pathreview/commit/f06165a1bdd781cd4331f20aaf30103c7e5a8451

**PLAN.md:** https://github.com/ujval9/pathreview/blob/test/106-restore-basic-profile-fixture/PLAN.md

**Walkthrough video:** Not recorded.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. First established a baseline on `main`
(d5f196d): `make test-unit` = 53 failed / 375 passed and `ruff` = 182 errors,
both pre-existing and unrelated to this issue. Then completed PLAN sub-tasks 1–5:
read `ResumeParser._detect_sections` and `RepoAnalyzer.parse` to lock the exact
shapes, authored `tests/fixtures/sample_profiles/basic_profile.json` (GitHub
username, multi-section resume, portfolio URL, two GitHub-API-shaped repos), and
added a `tests/unit/test_sample_profiles.py` schema test. The reproduction
integration test now passes (`make test-integration` → 3 passed) and
`make test-unit` is 53 failed / 378 passed — the same 53 pre-existing failures
plus my 3 new passing unit tests, i.e. no new failures.

**Next steps:**
Run the full self-review checklist (`make check`, read the diff, verify commit
and branch conventions), fill in the PR template, and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** _pending — filled in once the PR is opened_

**Branch:** `test/106-restore-basic-profile-fixture`

**What you built:**
Restored the missing shared sample-portfolio fixture
(`tests/fixtures/sample_profiles/basic_profile.json`) as a realistic portfolio —
a GitHub username, a multi-section resume, and two repositories shaped like the
GitHub API dicts the ingestion parsers read — plus a `conftest.py` loader and
unit/integration tests that exercise it.

**Tests added or updated:**
- `tests/integration/test_sample_profile_fixture.py` — loads the fixture and
  feeds it through `RepoAnalyzer` and `ResumeParser`.
- `tests/unit/test_sample_profiles.py` — validates the fixture's schema so
  `make test-unit` covers the change.
- `tests/conftest.py` — added the `basic_profile` loader fixture.

**Self-review confirmation:** [x] make check passes (no new failures vs. documented pre-existing baseline)  [x] make test-unit passes (no new failures vs. documented pre-existing baseline)

**Draft PR feedback received from:** none
