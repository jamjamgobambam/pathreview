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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [updated on GitHub]

**Reproduction summary:**
Reproduced the issue locally by running `.venv/Scripts/pytest tests/unit/test_readme_scorer.py -q`. Observed `AssertionError: assert 51 > 100` in `test_readme_with_all_quality_signals` because the mock `readme` fixture string only contains 51 words.

**PLAN.md link:** [https://github.com/Nanzib/pathreview/blob/fix/156-readme-scorer-fixture/PLAN.md](https://github.com/Nanzib/pathreview/blob/fix/156-readme-scorer-fixture/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:** None.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all sub-tasks from `PLAN.md`. Expanded the mock `readme` string fixture in `tests/unit/test_readme_scorer.py` from 51 words to ~530 words. Added realistic project description, architecture overview, installation steps, configuration flags, and contributing guidelines while maintaining all required Markdown quality signals (`#` headers, badge images, code snippets, demo links).

**Next steps:**
Verify test suite execution with `pytest`, commit changes, push working branch to remote fork, open Pull Request against upstream repository, and submit final branch link.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [Replace with live PR link after opening PR]

**Branch:** fix/156-readme-scorer-fixture

**What you built:**
Expanded the inline mock `readme` fixture string in `tests/unit/test_readme_scorer.py` from 51 words to ~530 words. This ensures `TestReadmeScorer.test_readme_with_all_quality_signals` satisfies both `data["word_count"] > 100` and `data["word_count_category"] == "comprehensive"` as expected by the scorer logic.

**Tests updated:**
Updated `tests/unit/test_readme_scorer.py` (`TestReadmeScorer.test_readme_with_all_quality_signals`). Covered word count thresholds (>500 words for comprehensive tier), category classification ("comprehensive"), and verified that installation, usage, tech stack, badge, and demo link detection signals remain functional.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none