# Solution Plan — Issue #157

**Issue:** [Relevance scorer "partial overlap" test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)
**Branch:** `fix/157-relevance-scorer-fixture`
**Tier:** 1 (bug / tests)

## Context / Problem
There is a broken unit test in `tests/unit/test_relevance_scorer.py`. The test
`test_query_with_partial_overlap` is meant to check that a query which only *partly* matches a
chunk gets a middle-range relevance score. But the test data is wrong: the query
`"Python Django web framework"` is scored against a chunk that actually contains **all four** of
those words, so it's really a full match, not a partial one. The scorer correctly returns `1.0`,
while the test expects a score below `0.9`, so the test fails even though the scoring code is
working correctly. The fault is in the test fixture, not the scorer.

## Reproduction
Environment: Python 3.11+ virtual env with dev dependencies installed (`pip install -e ".[dev]"`).
No Docker or database is required — this test only imports the scorer.

Command:
```
pytest tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap -q
```

- **Expected:** test passes (score in the partial range `0.3 < score < 0.9`).
- **Actual:** test fails:
  ```
  >   assert 0.3 < score < 0.9
  E   assert 1.0 < 0.9
  ...
  [info] relevance_scored  avg_score=1.0 chunks_count=1 query_len=4
  ```
Running the whole file gives `1 failed, 18 passed` — this is the only failing test.

## Root cause (traced through the code)
- `RelevanceScorer.score()` in `rag/evaluator/relevance_scorer.py` computes, per chunk,
  `overlap = len(query_tokens & chunk_tokens)` then `relevance = overlap / len(query_tokens)`
  (lines 40–41), and returns the average across chunks capped at `1.0` (line 50).
- `_tokenize()` (lines 52–62) is simply `text.lower().split()` — lowercase + whitespace split,
  with no punctuation stripping and no stopword removal.
- For this test: query tokens = `{python, django, web, framework}` (4 tokens). The chunk
  `"Django is a Python web framework for rapid development"` contains all four → `overlap = 4`,
  `score = 4/4 = 1.0`. The assertion `0.3 < 1.0 < 0.9` is therefore False.

So the scorer behaves correctly; the fixture was mislabeled "partial overlap" while actually
providing full overlap.

## Proposed fix
Edit **only** the fixture chunk in `test_query_with_partial_overlap` so it contains *some but not
all* of the query words. Dropping "Django" is the smallest clear change:

```python
# query stays: "Python Django web framework"  -> {python, django, web, framework}
"text": "This Python web framework is great for rapid development"
# contains python, web, framework (3) but NOT django -> 3/4 = 0.75, inside 0.3–0.9
```

## Files to change
- `tests/unit/test_relevance_scorer.py` — one line (the chunk `text` inside
  `test_query_with_partial_overlap`, ~line 52). No other files.
- The scorer (`rag/evaluator/relevance_scorer.py`) is **not** changed — it is already correct.

## Sub-tasks (in order)
1. Edit the chunk string in `test_query_with_partial_overlap`.
2. Run just that test → confirm it passes.
3. Run the whole file (`pytest tests/unit/test_relevance_scorer.py -q`) → confirm 19 passed.
4. Run `make test-unit` → confirm no regressions elsewhere.
5. Run `make check` (ruff / black / mypy).
6. Commit with a Conventional Commit message, e.g. `test(rag): fix partial-overlap fixture in relevance scorer test` with footer `Fixes #157`.
7. Open a PR using `.github/PULL_REQUEST_TEMPLATE.md`.

## Risks & edge cases
- **Do not modify `_tokenize()` or the scorer.** Changing tokenization would break
  `test_tokenization`, `test_common_words_not_preventing_scoring`, and
  `test_special_characters_ignored`, and would be the wrong fix (the scorer is correct).
- **Keep the new score strictly inside `0.3 < score < 0.9`.** With 4 query tokens, matching 2 or 3
  words gives `0.5` or `0.75` — both safe. Matching all 4 → `1.0` (fails); matching only 1 →
  `0.25` (fails the lower bound).
- **No trailing punctuation on kept words** — the tokenizer doesn't strip punctuation, so
  `"framework."` would not match `"framework"`.
- **Verify the other 18 tests still pass** — the change is isolated (the chunk is inline and not
  shared), so no other test should be affected.

## Verification
- Before the fix: `test_query_with_partial_overlap` fails with `assert 1.0 < 0.9`.
- After the fix (Week 9): that test passes, the full file is `19 passed`, and
  `make check && make test-unit` both succeed.

## Alternatives considered
- **Change the query instead of the chunk** (add a query word absent from the chunk) — also valid;
  chose the chunk edit as the smaller, clearer change.
- **Loosen the assertion to allow `1.0`** — rejected; that would defeat the purpose of a
  "partial overlap" test.
- **Change `_tokenize` / the scorer** — rejected; the scorer is correct and this would break other
  tests.
