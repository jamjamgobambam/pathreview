## Solution plan

**Issue:** README scorer unit test failure caused by incorrect word-count expectation in test fixture.

### Understand
The failure occurs in `tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals`.
The test constructs a README sample and asserts `word_count > 100`, but the sample text is only 51 words.
Expected behavior: the test should either use a README sample that meets the expected `comprehensive` threshold, or the scorer logic/threshold should be adjusted to match realistic expectations for the sample.

### Map
Files and modules involved:
- `tests/unit/test_readme_scorer.py` — test fixture and assertions
- `agent/tools/readme_scorer.py` — scoring implementation and word-count categorization
- potentially `pyproject.toml` or test config if the environment setup affects test expectations

### Plan
1) Reproduce & capture evidence
   - Run the failing test and capture output: `pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -q`.
   - Save terminal output and screenshot named `readme_bug_reproduction.png` (keeps evidence for the PR/issue).

2) Inspect the test fixture & scorer code
   - Open `tests/unit/test_readme_scorer.py`, locate the `readme` sample used in the failing test and compute its word count (quick one-liner: `python -c "print(len(open('tests/unit/test_readme_scorer.py').read().split()))"` scoped to the sample or manually count the sample words).
   - Open `agent/tools/readme_scorer.py` to confirm the current word-count categorization logic (`<100 => minimal`, `100-499 => adequate`, `>=500 => comprehensive`).

3) Decide the least-invasive corrective action
   - Option A (preferred): Extend the test's `readme` sample so it legitimately exceeds 100 words. This keeps scorer thresholds intact and makes the test reflect a realistic "comprehensive" example.
   - Option B: If project policy expects the sample to remain short, update the test assertion to match the sample (e.g., assert `word_count >= 50` and adjust `word_count_category` expectations) or lower the threshold in `readme_scorer.py`.
   - Document the chosen approach in the test or a short PR note.

4) Implement the chosen fix (detailed steps for Option A)
   - Edit `tests/unit/test_readme_scorer.py`:
     - Append a realistic paragraph of filler text to the `readme` variable so the sample exceeds 100 words.
     - Add a one-line comment above the sample explaining why it is long (prevents accidental shrinkage).
   - Run the focused test: `pytest tests/unit/test_readme_scorer.py -q` and then run the full test suite: `pytest -q`.

5) Verify, commit, and document
   - Verify all tests pass locally.
   - Commit with a clear message: `test: extend README sample to satisfy comprehensive word-count for readme_scorer test`.
   - Include `readme_bug_reproduction.png` in the commit if you want to archive the failure evidence.
   - In the PR description, explain why the sample was extended and link the failing output screenshot.

6) Follow-up (optional)
   - Add a brief note in repository docs/tests guidelines explaining why some fixture examples intentionally exceed thresholds.
   - If multiple tests rely on the same threshold, consider adding a small helper to generate long sample readmes for tests to avoid manual filler text.

### Inputs & outputs
Input: existing unit test case and scorer behavior.
Output: updated test fixture and/or scorer expectations that make the test pass for a valid README sample while preserving the intended quality assessment.

### Risks & unknowns
- If the test is intentionally designed to validate a long README, changing the sample may hide a separate bug in word-count calculation.
- If the scoring thresholds are wrong, the test fix should not be the only change; the scoring logic may need review.

### Edge cases
- README content with markdown code blocks and badges should still count words correctly.
- Empty or whitespace-only README content must remain categorized as minimal.
- Short readmes that contain installation/usage/demo signals should not be incorrectly treated as comprehensive unless the word count qualifies.