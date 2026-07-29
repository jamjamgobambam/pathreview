# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The README scorer unit test named `test_readme_with_all_quality_signals` uses a README fixture containing only about 51 words, but the test expects the scorer to report more than 100 words and classify it as `comprehensive`. Because the fixture does not satisfy the conditions being asserted, the test fails even when the scorer correctly handles the shorter README. A successful fix will align the fixture with the intended comprehensive-README scenario, most likely by extending it beyond 100 words while preserving the other quality signals being tested. This issue is localized to `tests/unit/test_readme_scorer.py`.

**Issue-selection reasoning:**

I selected this Tier 1 issue because it is a self-contained test-fixture problem involving one clearly identified unit-test file rather than a change across multiple application modules. I can explain the current failure, identify the expected before-and-after behavior, and reproduce it with the command provided in the issue. The scope is appropriate for my first contribution to this codebase because the expected fix is limited, testable, and unlikely to affect unrelated application behavior. I also confirmed that the issue does not list any blockers or unresolved dependencies.

**Relevant code:** `tests/unit/test_readme_scorer.py`

**Expected before-and-after behavior:**

Before the fix, the test fixture contains too few words to meet its own `word_count > 100` and `comprehensive` assertions. After the fix, the fixture and assertions will describe the same intended scenario, allowing the test to validate the README scorer accurately.

**Branch name:** `test/156-readme-scorer-fixture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Issue claimed:** [x] Claim comment added to GitHub issue

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ryandej/pathreview/commit/d74b9f2

**Reproduction summary:**
I reproduced the issue locally by running `python -m pytest tests/unit/test_readme_scorer.py -q`. The test failed at `TestReadmeScorer::test_readme_with_all_quality_signals` because the README fixture produced `word_count=51`, while the test asserts `data["word_count"] > 100` and expects the comprehensive README path.

**PLAN.md link:** https://github.com/ryandej/pathreview/blob/test/156-readme-scorer-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded — recommended, not graded.

**Blockers or open questions:**
No major blockers. The main open question is whether maintainers prefer expanding the fixture to match the existing assertions or changing the assertion if the intended behavior is for the shorter README to remain minimal.
