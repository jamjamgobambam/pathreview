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