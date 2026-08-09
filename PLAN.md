# Solution Plan — Issue #156

**Issue:** [README scorer test fixture is too short for its own word-count assertion #156](https://github.com/ascherj/pathreview/issues/156)

### Understand
The unit test `test_readme_with_all_quality_signals` inside `tests/unit/test_readme_scorer.py` checks whether a high-quality README file gets categorized as "comprehensive". The scorer in `agent/tools/readme_scorer.py` requires a word count exceeding 100 words (`word_count > 100`) to award that tier. However, the mock README string fixture provided in the test currently contains only 51 words. Running `pytest` outputs `category=minimal word_count=51` and triggers an `AssertionError: assert 51 > 100`. The root cause is a deficient test fixture, not a bug in the scorer's core evaluation logic.

### Map
* **Files involved:**
  * `tests/unit/test_readme_scorer.py` — Contains `TestReadmeScorer.test_readme_with_all_quality_signals` and the inline mock `readme` string fixture.
  * `agent/tools/readme_scorer.py` — The core `ReadmeScorer` class defining quality signal thresholds and word count calculations.

### Plan
1. **Locate fixture in test suite:** Open `tests/unit/test_readme_scorer.py` and inspect the multi-line string variable `readme` in `test_readme_with_all_quality_signals`.
2. **Expand README text fixture:** Add ~60–70 additional realistic words (adding detailed sections for configuration, contributing guidelines, or API endpoints) to bring the total word count to ~115–120 words.
3. **Preserve quality signals:** Ensure the added text maintains required Markdown structure (such as `#` headers, links, and code blocks) so other quality signal assertions do not break.
4. **Run test suite verification:** Execute `.venv/Scripts/pytest tests/unit/test_readme_scorer.py -q` in Git Bash to verify `assert data["word_count"] > 100` passes and the test turns green.

### Inputs & outputs
* **Input:** Expanded multi-line `readme` string passed to `scorer.execute({"readme_content": readme})` in `tests/unit/test_readme_scorer.py`.
* **Output:** A dictionary returned in `result.data` where `data["word_count"]` is an integer greater than 100 (e.g., 115) and `word_count_category` evaluates to `"comprehensive"`.

### Risks & unknowns
* **Risk 1 (`tests/unit/test_readme_scorer.py`):** Adding new text could accidentally dilute keyword density or section ratios expected by other quality checks in `agent/tools/readme_scorer.py`.
* **Risk 2 (`agent/tools/readme_scorer.py`):** The internal word count parser might split tokens differently on code snippets vs plain text, so raw word count must be verified against `data["word_count"]` rather than a basic python `.split()`.

### Edge cases
1. **Boundary condition (101 words):** Ensuring the fixture clearly exceeds 100 words (e.g., 115 words) rather than sitting right at 100, which would fail strict inequality `> 100`.
2. **Markdown syntax noise:** Ensuring code blocks (` ```bash `) and markdown links in the fixture are handled gracefully by the scorer without affecting header detection.