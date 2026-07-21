## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/156]

**Issue title:** [README scorer test fixture is too short for its own word-count assertion]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The README scorer in tests/unit/test_readme_scorer.py has a test whose fixture and assertions disagree with each other. The test test_readme_with_all_quality_signals expects a "comprehensive" README with a word count above 100, but the sample README it actually passes in only contains about 51 words. Because the scorer correctly reports that low count, the assertion word_count > 100 fails — so the test flags a problem that doesn't exist in the scoring logic itself. This affects the test suite, not the scorer implementation: the failure is a mismatch between the test data and the behavior being asserted. A successful fix makes the test internally consistent — either by enlarging the fixture README so it genuinely qualifies as comprehensive, or by adjusting the assertions to match what a ~51-word README should score — so the test passes and actually validates the intended scorer behavior.]

**Branch name:** [fix/156-resume-scorer-test]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger