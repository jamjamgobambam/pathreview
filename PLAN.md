## Solution plan

**Issue:** ascherj#156 - README scorer test fixture is too short for its own word-count assertion

### Understand
The unit test `TestReadmeScorer.test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` validates that a high-quality README produces a word count greater than 100 (`assert data["word_count"] > 100`). However, the string fixture defined inside the test only contains 51 words. The scorer algorithm accurately counts the 51 words, causing `pytest` to fail with `AssertionError: assert 51 > 100`. The scorer logic itself functions correctly; the issue is entirely that the test fixture string is too short.

### Map
* `tests/unit/test_readme_scorer.py` (specifically the `test_readme_with_all_quality_signals` test method)

### Plan
1. Open `tests/unit/test_readme_scorer.py` and locate `test_readme_with_all_quality_signals`.
2. Expand the inline `readme` multi-line string fixture by adding realistic project documentation details (e.g., prerequisites, detailed configuration options, API usage, and contributing guidelines).
3. Ensure the updated fixture text comfortably exceeds 100 words while retaining all existing quality markers (headings, badges, code blocks, links, list items).
4. Run `pytest tests/unit/test_readme_scorer.py -q` to verify the assertion passes and all 23 unit tests pass.

### Inputs & outputs
* **Input:** An expanded Markdown string fixture for `test_readme_with_all_quality_signals` containing > 100 words.
* **Output:** `pytest` execution where `result.data["word_count"] > 100` evaluates to `True` without breaking surrounding assertions.

### Risks & unknowns
* Accidentally altering existing quality signals (like removing badges, links, or code blocks) while expanding the text, which could cause lower-level feature checks in `ReadmeScorer` to fail.
* Adding text inside code blocks that might be parsed or excluded from word counts differently depending on how `ReadmeScorer` calculates length.

### Edge cases
* Ensuring prose word count is well over 100 (e.g., 120+ words) so minor variations in how the scorer splits tokens or strips Markdown syntax don't drop the word count back below 100.