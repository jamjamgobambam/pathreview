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
