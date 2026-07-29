# Issue #157 reproduction

Issue: [Relevance scorer “partial overlap” test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

## Environment

- Reproduced on Windows with Python 3.14.4
- Focused dependencies: `pytest` and `structlog`
- Reproduction date: 2026-07-28

## Steps

1. Use the original `test_query_with_partial_overlap` fixture in
   `tests/unit/test_relevance_scorer.py`:

   ```python
   query = "Python Django web framework"
   chunks = [
       {
           "text": "Django is a Python web framework for rapid development"
       },
   ]
   ```

2. Run:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/unit/test_relevance_scorer.py -q
   ```

## Observed result

The focused test file reports `1 failed, 18 passed`. The failing assertion is:

```text
assert 0.3 < score < 0.9
E       assert 1.0 < 0.9
```

All four unique query tokens—`python`, `django`, `web`, and `framework`—also
occur in the chunk. `RelevanceScorer.score()` therefore computes `4 / 4` and
correctly returns `1.0`; the fixture does not represent partial overlap.

## Expected result

The partial-overlap fixture should contain some, but not all, query tokens so
the score falls strictly between the test's `0.3` and `0.9` bounds.
