## Solution plan

**Issue:** 
Title:README scorer test fixture is too short for its own word-count assertion
Link: https://github.com/ascherj/pathreview/issues/156

### Understand
The root cause is a mismatch between the test fixture and the scorer’s documented behavior. The test `test_readme_with_all_quality_signals` expects a README with `word_count > 100` and `word_count_category == "comprehensive"`, but the multiline README fixture in the test only produces about 51 words. The expected behavior is that a “comprehensive” README should satisfy the scorer’s current threshold, while the actual behavior is that the current fixture is too short and the assertion fails even though the scorer is working correctly.

### Map
The main files are `tests/unit/test_readme_scorer.py` and `agent/tools/readme_scorer.py`. The scorer implementation in `ReadmeScorer._score_readme` defines the word-count categories, and the unit test currently supplies the fixture and assertions that do not line up with that implementation. I expect the fix to touch only the unit test file unless the plan changes after review.

### Plan
1. Update the README fixture in `tests/unit/test_readme_scorer.py` so it is long enough to satisfy the current `comprehensive` threshold.
2. Keep the existing quality-signal assertions so the test still verifies installation, usage, badges, demo link, tech stack, and overall score.
3. Run the focused unit test to confirm the fixture now produces the expected word count and category.
4. If needed, refine the test data to stay readable while still being clearly above the threshold.

### Inputs & outputs
Input is the existing README fixture string in the unit test. The change should produce a test README that reflects a truly long-form, high-quality README and causes the scorer to return a word count above the comprehensive threshold without changing the scorer logic.

### Risks & unknowns
The main risk is making the test fixture unnecessarily large or awkward to maintain. Another risk is accidentally changing the test in a way that weakens what it is trying to verify, such as lowering the assertions instead of matching the scorer’s current rules. I am still confirming whether the test should assert `comprehensive` specifically or whether a separate test should cover that category more directly.

### Edge cases
The updated test should still be readable and should not depend on fragile wording that could change the word count unexpectedly. It should also remain stable if whitespace or formatting in the fixture changes slightly, and it should continue to validate the other quality signals independently of the word-count threshold.
