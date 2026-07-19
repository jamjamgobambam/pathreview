## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The test `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py`
asserts that a sample README fixture should score `word_count > 100` and fall into
the `"comprehensive"` word-count category. However, the scorer's actual thresholds
(defined in `agent/tools/readme_scorer.py`) require 500+ words for the "comprehensive"
category — the fixture README only contains about 51 words, so the test fails even
though the scorer itself is working correctly. The fix means extending the fixture
README with realistic content so it genuinely exceeds 500 words, and correcting the
assertion to check against the right threshold, so the test actually validates the
scorer's intended behavior instead of a mismatched expectation.

**Branch name:** fix/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**

- **Understanding:** I can explain this without re-reading the issue: the test
  `test_readme_with_all_quality_signals` asserts a README scores as "comprehensive"
  once it exceeds 100 words, but the scorer's real threshold (in
  `agent/tools/readme_scorer.py`) requires 500+ words for that category — the
  fixture README is only ~51 words, so the test fails even though the scorer is
  behaving correctly. Before the fix: `pytest` fails on `assert 51 > 100`. After:
  the fixture contains 500+ realistic words and the assertions check the actual
  threshold, so the test validates real scorer behavior instead of a mismatched
  expectation.

- **Tier fit:** Tier 1 — self-contained, touches one test file and one fixture,
  no cross-module understanding required. Appropriate as my first open-source
  contribution.

- **Codebase readiness:** I read `_score_readme` in `ReadmeScorer` in full,
  including the exact word-count boundaries (`<100` minimal, `<500` adequate,
  else comprehensive) and the regex checks for installation/usage/badges/demo/tech-stack
  sections. I also read the full test file, including how
  `test_word_count_category_comprehensive` already builds a 700-word fixture the
  same way I'll need to for this fix.

- **Scope and time:** Checked issue comments and the ledger — [X] other student(s)
  also claimed this issue, which I'm fine with since claims are non-exclusive.
  Estimated time: 1-2 hours, well within the Tier 1 range and comfortably
  achievable before the Week 9 deadline. No blockers or dependencies mentioned
  in the issue.