## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In tests/unit/test_readme_scorer.py, the test_readme_with_all_quality_signals test has expectations that don't match the scorer's actual behavior. The fixture README is only 51 words long, but the test expects it to have a word count over 100 and be classified as "comprehensive", even though agent/tools/readme_scorer.py only assigns that category to READMEs with more than 500 words. Because of this mismatch, the test fails even when the scoring logic is working correctly. A successful fix would either expand the fixture so it meets the "comprehensive" threshold or update the assertions to match the category the existing fixture should receive, ensuring the test accurately validates the scorer's behavior.

**Selection reasoning:**
I chose this as a Tier 1 issue since this is my first time contributing to a codebase this size, and it let me practice navigating the repo and confirming a bug before touching anything higher-risk. The scope fit well for a first issue: it's isolated to a single test file (`tests/unit/test_readme_scorer.py`) and the scorer logic it tests (`agent/tools/readme_scorer.py`), with no Docker, database, or API dependencies involved. It also has a clear, objective pass/fail signal — running `pytest tests/unit/test_readme_scorer.py -q` — so I can verify my fix actually resolves the issue rather than just guessing.

**Branch name:** fix/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/FremahA/pathreview/commit/cbf5072bccd021c70ee2621447e48c0b24eac642

**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` and observed that `test_readme_with_all_quality_signals` fails. The test fixture contains only 51 words, so the scorer correctly reports `word_count=51` and `word_count_category="minimal"`, causing the test's expectations of `word_count > 100` and `"comprehensive"` to fail.

**PLAN.md link:** https://github.com/FremahA/pathreview/blob/fix/156-readme-scorer-fixture-word-count/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: extended the README fixture in `test_readme_with_all_quality_signals` (`tests/unit/test_readme_scorer.py`) from 51 to 586 words, adding realistic README content while preserving every original quality-signal marker (installation, usage, badges, demo link, tech stack). Ran `make test-unit` — the file now passes 23/23, up from 22/23, with no new failures introduced elsewhere in the suite (52 pre-existing failures exist across unrelated files). Ran `make check`/`make lint` — no new lint errors from this change (182 pre-existing `F841` errors exist in `tests/unit/test_tech_detector.py`, unrelated). Committed and pushed the fix.

**Next steps:**
Run `make typecheck` to confirm no new mypy errors, open a draft PR early for peer/mentor feedback in Slack, and address any feedback before marking the PR ready for review.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/979

**Branch:** fix/156-readme-scorer-fixture-word-count

**What you built:**
Extended a test fixture in `tests/unit/test_readme_scorer.py` so `test_readme_with_all_quality_signals` actually satisfies its own assertions — the fixture is now 586 words (past the scorer's 500-word "comprehensive" threshold), while still exercising every quality signal (installation, usage, badges, demo link, tech stack) the test was designed to check. No production code was changed; the scorer logic in `agent/tools/readme_scorer.py` was already correct.

**Tests added or updated:**
Updated `tests/unit/test_readme_scorer.py` — specifically the fixture inside `test_readme_with_all_quality_signals`. No new test files needed since this was a fix to an existing test's data, not new behavior.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: this change touches only tests/unit/test_readme_scorer.py, a test-data-only edit. make test-unit: file passes 23/23, no new failures (52 pre-existing failures exist across ~10 unrelated files). make lint: no new errors (182 pre-existing F841 errors exist only in test_tech_detector.py). make typecheck: no new errors (103 pre-existing errors exist across 26 unrelated files, e.g. api/routes/profiles.py, core/services/profile_service.py). "Passes" here means introduces no new failures, per this week's pre-existing-failures guidance — none of the pre-existing failures touch the file changed in this PR.)

**Draft PR feedback received from:** none — no course Slack channel was available/confirmed at time of submission