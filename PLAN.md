## Solution plan

**Issue:** [README scorer test fixture is too short for its own word-count assertion](https://github.com/ascherj/pathreview/issues/156)

### Understand
`test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` asserts `word_count > 100` and `word_count_category == "comprehensive"`, but its inline fixture README is only 51 words. The logic in `agent/tools/readme_scorer.py`, `word_count_category` is `"minimal"` if it is below 100 words, `"adequate"` from 100–499 words, and `"comprehensive"` only at 500+ words. So the fixture needs 500+ words, not just over 100, for the assertion to pass. Expected: test passes and meets the "comprehensive" path. Actual: test fails at `assert data["word_count"] > 100` (currently 51), so the "comprehensive" branch is never even reached.

### Map
- `tests/unit/test_readme_scorer.py` (`test_readme_with_all_quality_signals`), update the README test fixture (only file I except to change).
- `agent/tools/readme_scorer.py` (`ReadmeScorer._score_readme`) reference only to confirm the 500-word requirement and the patterns for installation, usage, badges, demo link, and tech stack.

### Plan
1. Add more realistic content to the README fixture so it is over 500 words.
2. Keep all the existing sections that the test checks, including:
    - Installation with a code block
    - Usage with a code block
    - badges (![...](...))
    - Tech Stack
    - a demo link ([Try it here](...))
3. Run `.venv/bin/pytest tests/unit/test_readme_scorer.py -v -k test_readme_with_all_quality_signals` to make sure that test passes.
4. Run the full `tests/unit/test_readme_scorer.py` file to make sure the other README scorer tests still pass.
5. Check that the overall score is still above `0.7` now that the README gets full credit for being over 500 words.

### Inputs & outputs
- Input: The README string inside `test_readme_with_all_quality_signals`.
- Output: A longer README fixture (500+ words) with the same sections and formatting. No changes to `agent/tools/readme_scorer.py`.

### Risks & unknowns
- Adding too much new formatting or extra headings could accidentally stop one of the regex checks from matching, so most of the added content should just be normal paragraphs.
- If the README ends up just under 500 words, the test could still fail. Aim for around 550 words to leave some room for future edits.

### Edge cases
- Count words the same way the scorer does by using whitespace-separated words (`str.split()`).
- Keep the existing Markdown format, including code blocks and bullet lists, since they already work with the scorer.