## Solution plan

**Issue:** [issue title and link]

### Understand
The root cause is that the README scorer test fixture does not match the scorer’s word-count categorization. Expected behavior: comprehensive fixture should be >500 words and satisfy the scorer’s signals.

### Map
Files: `tests/unit/test_readme_scorer.py`, `agent/tools/readme_scorer.py`
Functions: `ReadmeScorer._score_readme`, `TestReadmeScorer.test_readme_with_all_quality_signals`

### Plan
1. Verify current scorer threshold logic.
2. Update fixture to meet “comprehensive” criteria or adjust assertions to match intent.
3. Run pre-commit / mypy and confirm test passes.

### Inputs & outputs
Input: README test fixture text and scorer output.
Output: consistent test expectations with scorer behavior and passing unit test.

### Risks & unknowns
Risk: changing fixture may mask broader score logic issues.
Unknown: whether “comprehensive” category should be based on >500 words or more structural signals.

### Edge cases
- Empty README
- Minimal README with title only
- Adequate README between 100-500 words
- README with sections but low word count