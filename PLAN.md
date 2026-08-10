# Solution plan

**Issue:** README scorer test fixture is too short for its expected word-count category — Issue #156

### Understand

The issue is caused by a mismatch between the README content used in `test_readme_with_all_quality_signals` and the assertions in that test.

The README fixture contains only 51 words. However, the test expects the word count to be greater than 100 and expects the word-count category to be `comprehensive`.

The scorer currently categorizes the README as `minimal`, which matches its actual length. Based on the existing word-count tests, a README must contain more than 500 words to be categorized as `comprehensive`.

The expected behavior is for the test fixture to contain enough meaningful content to satisfy the comprehensive category. The actual behavior is that the fixture is too short, causing the test to fail.

### Map

The main files involved are:

- `tests/unit/test_readme_scorer.py`
  - Contains `test_readme_with_all_quality_signals`
  - Contains the short README fixture
  - Contains the failing assertions
  - Contains tests for the word-count categories

- `agent/tools/readme_scorer.py`
  - Contains the `ReadmeScorer` implementation
  - Calculates the README word count
  - Assigns the `minimal`, `adequate`, or `comprehensive` category
  - Calculates the overall README score

I expect the final change to mainly affect `tests/unit/test_readme_scorer.py`.

### Plan

1. Review `agent/tools/readme_scorer.py` to confirm the exact word-count thresholds used by the scorer.

2. Review the category tests in `tests/unit/test_readme_scorer.py` to confirm that more than 500 words is required for the `comprehensive` category.

3. Expand the README fixture in `test_readme_with_all_quality_signals` so that it contains more than 500 meaningful words.

4. Preserve the existing README quality signals, including installation instructions, usage instructions, features, technologies, badges, and a live demo link.

5. Run the focused test and the full README scorer test file to verify that the issue is fixed without breaking the other tests.

### Inputs & outputs

The input is a Markdown README string passed into:

```python
scorer.execute({"readme_content": readme})