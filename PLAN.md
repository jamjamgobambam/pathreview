# Week 8: Issue Reproduction and Solution Plan

## Issue

**Issue #156:** README scorer test fixture is too short for its own word-count assertion

**Issue Link:** https://github.com/ascherj/pathreview/issues/156

---

## Reproduction Steps

1. Open the local PathReview repository.
2. Switch to the `fix/156-readme-scorer-fixture` branch.
3. Activate the Python virtual environment.

```bash
source .venv/bin/activate
```

4. Run the failing test.

```bash
pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -v
```

5. Observe the failure:

```
assert 51 > 100
```

The README scorer reports:

- `word_count = 51`
- `word_count_category = "minimal"`

6. Run the complete README scorer test suite.

```bash
pytest tests/unit/test_readme_scorer.py -v
```

7. Verify the results:

- 23 tests collected
- 22 tests passed
- 1 test failed

The only failing test is:

```
test_readme_with_all_quality_signals
```

---

## Observed Failure

The failing test expects the sample README to contain more than 100 words and be classified as a comprehensive README.

However, the README fixture only contains 51 words.

The failing assertion is:

```python
assert data["word_count"] > 100
```

Actual result:

```
assert 51 > 100
```

---

## Root Cause

The README scoring implementation is working correctly.

The scorer classifies README files as:

- **minimal:** fewer than 100 words
- **adequate:** 100–499 words
- **comprehensive:** 500 words or more

The sample README used by `test_readme_with_all_quality_signals` contains only 51 words, so it is correctly classified as **minimal**.

The problem is the test fixture, not the production code.

---


## Files to Modify

```
tests/unit/test_readme_scorer.py
```

No changes are expected in:

```
agent/tools/readme_scorer.py
```

---

## Inputs and Outputs

### Input

The test passes a Markdown README string to the scoring logic used by
`test_readme_with_all_quality_signals` in:

```
tests/unit/test_readme_scorer.py
```

The fixture includes README content such as headings, installation instructions,
usage information, features, technology details, badges, and a demo link.

### Current Output

With the current 51-word fixture, the scorer returns:

```
word_count = 51
word_count_category = "minimal"
```

This output is consistent with the thresholds in:

```
agent/tools/readme_scorer.py
```

### Expected Output After the Fix

After expanding the fixture to at least 500 words, the scorer should return:

```
word_count >= 500
word_count_category = "comprehensive"
```

The other quality-signal results should remain unchanged, and
`test_readme_with_all_quality_signals` should pass.


---

## Planned Solution

1. Update the README fixture in `test_readme_with_all_quality_signals`.
2. Preserve all existing README quality sections:
   - Installation
   - Usage
   - Features
   - Tech Stack
   - Badges
   - Demo Link
3. Expand the README so it contains **at least 500 words**, allowing it to be classified as **comprehensive** while preserving all existing quality signals.
4. Update the word-count assertion, if necessary, so it matches the scorer's documented thresholds.
5. Verify that the fixture still tests all quality signals.
6. Re-run the failing test.

```bash
pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -v
```

7. Re-run the complete README scorer test suite.

```bash
pytest tests/unit/test_readme_scorer.py -v
```
---

## Risks and Unknowns

- In `tests/unit/test_readme_scorer.py`, adding text without preserving headings such as Installation, Usage, Features, and Tech Stack could cause the fixture to stop testing one or more intended quality signals.

- In `agent/tools/readme_scorer.py`, the word-count logic may count Markdown elements differently than expected. The updated fixture should therefore be validated by running the scorer rather than relying only on a manual word count.

- Changing the thresholds in `agent/tools/readme_scorer.py` would affect the dedicated minimal, adequate, and comprehensive category tests. The planned fix should therefore remain limited to the test fixture unless further investigation shows the production logic is incorrect.

- The existing assertion `data["word_count"] > 100` may need to be reviewed so it accurately reflects the documented threshold for a comprehensive README.

---

## Edge Cases

- README with exactly 99 words
- README with exactly 100 words
- README with exactly 499 words
- README with exactly 500 words

The updated fixture should clearly fall within the comprehensive category while keeping all quality indicators.

---

## Validation Plan

Run:

```bash
pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -v
```

Then run:

```bash
pytest tests/unit/test_readme_scorer.py -v
```

Expected result:

- 23 tests collected
- 23 tests passed