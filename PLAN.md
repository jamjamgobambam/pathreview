@"
## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion - https://github.com/ascherj/pathreview/issues/156

### Understand
The test test_readme_with_all_quality_signals in tests/unit/test_readme_scorer.py asserts that a "high quality" fixture README scores word_count > 100 and word_count_category == "comprehensive". In agent/tools/readme_scorer.py, _score_readme categorizes word count as: <100 = "minimal", 100-499 = "adequate", 500+ = "comprehensive". The fixture README used in the test contains only ~51 words. Locally reproducing the test confirms word_count=51, category="minimal" - well short of even "adequate," let alone "comprehensive." Expected behavior: the fixture should represent a genuinely comprehensive README and the test should validate that the scorer correctly identifies it as such. Actual behavior: the fixture is too short to satisfy its own assertions, so the test fails independent of whether the scorer logic is correct (it is - this is a test data bug, not a scorer bug).

### Map
- tests/unit/test_readme_scorer.py - contains the failing test and its fixture (primary file to edit)
- agent/tools/readme_scorer.py - the scorer being tested; read to confirm category thresholds, not expected to change
- No other files reference this specific fixture or test, based on a repo-wide search for test_readme_with_all_quality_signals

### Plan
1. Decide the fix approach: extend the fixture to genuinely exceed 500 words (true "comprehensive"), since that best matches the test's intent to validate a top-tier README with every quality signal present.
2. Extend the existing fixture's content (e.g. add realistic Configuration, Contributing, and expanded Features/Tech Stack sections) rather than padding with filler text, so the fixture stays meaningful and continues exercising all the quality-signal checks (installation, usage, badges, demo link, tech stack).
3. Re-run the target test locally to confirm word_count > 500 and word_count_category == "comprehensive" both pass.
4. Run the full test file (pytest tests/unit/test_readme_scorer.py -v) to confirm no other test in the suite was relying on the old fixture's exact word count or content.
5. Add a short comment near the fixture noting the word-count threshold it's designed to satisfy, so a future contributor doesn't accidentally shrink it below 500 words again.

### Inputs & outputs
Input: The fixture README string inside test_readme_with_all_quality_signals.
Output: An extended fixture string with >500 words, all existing structural elements preserved (installation, usage, badges, demo link, tech stack sections), so all nine assertions in the test pass together.

### Risks & unknowns
- Risk: Padding the fixture carelessly (e.g. repeating text) could make it look artificial and reduce the test's value as a realistic example; will write genuine, varied prose instead.
- Risk: Extending the fixture could push overall_score above 1.0 or otherwise change other passing assertions in the same test (e.g. the overall_score > 0.7 check) - need to re-verify all assertions still hold after editing.
- Unknown: PR #164 (open, unmerged, from an external contributor) claims to fix this by extending the fixture to only slightly over 100 words, which would not resolve word_count_category == "comprehensive" per the 500-word threshold - need to confirm this during implementation and note the discrepancy if relevant.
- Unknown: whether the maintainer intended "comprehensive" or would consider changing the assertion to "adequate" instead - will default to matching the fixture to the test's stated intent (a README with "all quality signals") unless feedback suggests otherwise.

### Edge cases
- Fixture must remain valid Markdown that the scorer's regex-based section detectors (installation, usage, badges, demo, tech stack) still correctly recognize after edits.
- Word count must clear 500 by a comfortable margin, not just barely (e.g. 501), to avoid flakiness if minor future edits are made.
- Must confirm the fixture doesn't accidentally trip has_readme or word_count_category into an unexpected category due to leading/trailing whitespace handling in _score_readme.
"@ | Out-File -FilePath PLAN.md -Encoding utf8