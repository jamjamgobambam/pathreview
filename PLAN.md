## Solution plan

**Issue:** [README scorer test fixture is too short for its own word-count assertion — #156](https://github.com/ascherj/pathreview/issues/156)

### Understand

The `test_readme_with_all_quality_signals` test is intended to verify that a comprehensive README containing all supported quality signals receives a high score. However, the test fixture contains only 51 words.

The README scorer categorizes content with fewer than 100 words as `minimal`, content from 100 through 499 words as `adequate`, and content with at least 500 words as `comprehensive`. The current fixture is therefore correctly categorized as `minimal`.

The test currently fails at:

```text
assert 51 > 100
```

The expected behavior is for the fixture to represent a comprehensive README and satisfy all assertions in the test. The actual behavior occurs because the fixture is too short for the scenario it is intended to represent. The root cause is in the test data, not the production scoring logic.

### Map

The following files and code are involved:

- `tests/unit/test_readme_scorer.py`
  - `TestReadmeScorer.test_readme_with_all_quality_signals`
  - Contains the fixture and assertions that currently fail.
  - This is the primary file expected to be modified.

- `agent/tools/readme_scorer.py`
  - `ReadmeScorer.execute`
  - `ReadmeScorer._score_readme`
  - Defines the word-count categories, quality-signal detection, and overall-score calculation.
  - This file was inspected to confirm the root cause but is not expected to require changes.

- `JOURNAL.md`
  - Records the reproduction steps, observed failure, and planning progress.

### Plan

1. Expand the README fixture in `test_readme_with_all_quality_signals` with meaningful, realistic project documentation.

2. Ensure the expanded fixture contains at least 500 words so that `ReadmeScorer` categorizes it as `comprehensive`.

3. Preserve all quality signals already tested by the fixture, including installation instructions, usage instructions, badges, a live-demo link, and a technology-stack section.

4. Run the affected test and the complete README scorer test file to verify that the corrected fixture passes without causing regressions.

5. Run the repository’s required checks with `make check` and `make test-unit` before submitting the change.

### Inputs & outputs

**Input:**

A README-formatted string passed to:

```python
scorer.execute({"readme_content": readme})
```

The fixture should contain realistic project documentation and all quality signals recognized by the scorer.

**Expected output:**

- `result.success` is `True`.
- `has_readme` is `True`.
- `word_count` satisfies the comprehensive README threshold.
- `word_count_category` is `"comprehensive"`.
- Installation, usage, badge, demo-link, and technology-stack signals are all detected.
- `overall_score` is greater than `0.7`.
- The affected unit test passes.

This change should correct the test fixture without changing the production scorer’s behavior.

### Risks & unknowns

- Adding only enough content to exceed 100 words would satisfy the first failing assertion but would still produce the `adequate` category. The fixture must contain at least 500 words to be categorized as `comprehensive`.

- Repetitive filler could make the test difficult to read and maintain. The added content should resemble meaningful project documentation.

- Changing or removing keywords could accidentally prevent the scorer from detecting one of the required quality signals.

- The test currently asserts that the word count is greater than 100 even though the `comprehensive` category begins at 500 words. Expanding the fixture beyond 500 words will satisfy both assertions, but it is unclear whether maintainers also want the assertion updated to reflect the comprehensive threshold directly.

- The complete unit-test suite may contain unrelated failures associated with other open issues. Those failures should be documented but not fixed as part of issue #156.

### Edge cases

- A README with fewer than 100 words should remain categorized as `minimal`.

- A README with 100 through 499 words should remain categorized as `adequate`.

- A README with exactly 500 words should be categorized as `comprehensive`.

- The expanded fixture must retain recognizable installation and usage wording.

- Badge Markdown and the live-demo link must remain in formats detected by the scorer.

- The fixture should continue to produce a valid result even with Markdown headings, lists, links, badges, and code blocks.