## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion #156

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The test `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` checks if a README is categorized as "comprehensive" when it has more than 100 words. However, the sample README text provided in the test only has about 51 words, causing `pytest` to fail with `assert 51 > 100`. A successful fix will expand the sample README fixture so it actually has over 100 words, allowing the test to pass correctly against the scorer's logic.

**Branch name:** fix/156-readme-scorer-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection & Scope Reasoning
I picked Issue #156 because it is a straightforward Tier 1 bug in the unit testing suite. It has clear steps to reproduce in `tests/unit/test_readme_scorer.py` and doesn't require changing complex core backend logic. This makes it a great fit for practicing codebase navigation, running tests, and getting used to the open-source workflow without getting bogged down in scope creep.