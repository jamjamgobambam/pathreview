## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156
**Issue title:** README scorer test fixture is too short for its own word-count assertion
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue affects the unit tests for the README scoring module in `tests/unit/test_readme_scorer.py`. The `test_readme_with_all_quality_signals` test asserts that a README fixture has a word count greater than 100, but the current test fixture string only contains ~51 words, causing `pytest` to fail. A successful fix will expand the mock README text in the fixture to over 100 words so that the word-count assertion passes as intended.

**Branch name:** fix/156-readme-scorer-fixture-length
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Paste your commit link here after pushing]
**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` on branch `fix/156-readme-scorer-fixture-length`. Confirmed `test_readme_with_all_quality_signals` fails with `AssertionError: assert 51 > 100` because the string fixture in `test_readme_scorer.py` has only 51 words.

**PLAN.md link:** [Paste link to PLAN.md in your GitHub fork]
**Walkthrough video (recommended):** 
**Blockers or open questions:**
None.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
- Located `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py`.
- Identified that the test fixture string had only ~51 words, causing `assert data["word_count"] > 100` and `assert data["word_count_category"] == "comprehensive"` to fail.
- Expanded the inline `readme` string fixture to exceed 500 words while maintaining all quality signals (badges, code blocks, links, lists, tech stack section).

**Next steps:**
- Run local linting and testing checks via `make check` and `make test-unit`.
- Open a Pull Request on GitHub and request peer review.
- Fill out Check-in 2 and submit the working branch URL to the course portal.

**Blockers:**
None.

---

### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/YOUR_PR_NUMBER_HERE
>Note: This is draft for now
**Branch:** fix/156-readme-scorer-fixture-length
**What you built:**
Expanded the mock README fixture string inside `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` to >500 words. This resolves the failing `word_count` and `word_count_category` assertions without changing any underlying scoring algorithm logic in `agent/tools/readme_scorer.py`.

**Tests added or updated:**
- `tests/unit/test_readme_scorer.py`: Expanded the `readme` text string fixture inside `test_readme_with_all_quality_signals`. The updated test covers the scenario where a README containing all quality signals (badges, installation, usage, demo links, tech stack) also meets the word count threshold required to qualify for the `"comprehensive"` word count category.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
**Draft PR feedback received from:** none