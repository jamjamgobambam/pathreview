# Module 3 Journal — PathReview

## Week 7 — Issue selection

**Issue link:** [paste GitHub issue #156 link here]

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue appears to involve a mismatch between a README scorer test fixture and the word-count assertion used by the test. The fixture text is probably shorter than the scorer expects, so the test does not accurately represent the condition it is trying to check. A successful fix would make the test fixture and assertion consistent, either by updating the fixture text or adjusting the test expectation after confirming the intended behavior. This seems scoped to the README scoring tests or related test fixtures, which makes it a manageable Tier 1 issue.

**Why this issue is a good fit:**
I chose this issue because it is labeled Tier 1 and good first issue, and it appears to be limited to the test/fixture layer rather than a large architectural change. The likely reproduction path is clear: run the relevant scorer tests, inspect the failing assertion, and compare the fixture content against the expected word-count condition. The main risk is understanding the scorer’s intended behavior before changing the test, so I will verify whether the fixture or assertion is the incorrect part before implementing a fix.

**Branch name:** fix/156-readme-scorer-word-count-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [(https://github.com/ascherj/pathreview/commit/10ff199b8c4588b2efeca1dc710bf8b7535d4228)]

**Reproduction summary:**
I reproduced issue #156 by running `.\.venv\Scripts\python.exe -m pytest "tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals" -v`. The relevant failure shows that `test_readme_with_all_quality_signals` (assertion `assert data["word_count"] > 100`, which fails as `assert 51 > 100`) depends on a README scorer fixture whose text does not satisfy the word-count condition being asserted. This confirms that the issue is located in the README scorer test or fixture setup, and the next step is to determine whether the fixture should be lengthened or the assertion should be adjusted based on the intended scorer behavior.

<!-- NOTE: The word count (51), test name, and assertion above were confirmed on my machine.
     Re-run the command yourself and confirm the same "assert 51 > 100" output before pushing. -->

**PLAN.md link:** [https://github.com/toquangminh/pathreview/blob/fix/156-readme-scorer-word-count-fixture/PLAN.md]

**Blockers or open questions:**
I still need to confirm whether the correct fix is to update the fixture text, adjust the assertion, or change scorer behavior. I will inspect the scorer implementation before making the Week 9 fix.