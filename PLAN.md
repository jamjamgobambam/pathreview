## Solution plan

**Issue:** Relevance scorer “partial overlap” test fixture actually has full query overlap — https://github.com/ascherj/pathreview/issues/157

### Understand

The issue is in the unit test `test_query_with_partial_overlap`.

The test query is:

```text
Python Django web framework
```

The test chunk is:

```text
Django is a Python web framework for rapid development
```

All four query words—`Python`, `Django`, `web`, and `framework`—are present in the chunk. Because all query words match, `RelevanceScorer.score()` correctly returns `1.0`.

However, the test expects the score to be less than `0.9` because it is intended to test partial overlap.

Expected behavior:

* A partial-overlap fixture should contain only some query words.
* The resulting score should be greater than `0.0` and less than `1.0`.

Actual behavior:

* The fixture contains all query words.
* The scorer returns `1.0`.
* The test fails with `assert 1.0 < 0.9`.

The likely fix is to correct the test fixture rather than change the production scoring logic.

### Map

The following files and components are involved:

* `tests/unit/test_relevance_scorer.py`

  * Contains `test_query_with_partial_overlap`.
  * Contains the incorrect test query, chunk, and assertion.
  * This is the main file expected to change.

* `rag/evaluator/relevance_scorer.py`

  * Contains the `RelevanceScorer` class and `score()` method.
  * This file is used to confirm how the overlap score is calculated.
  * No production-code change is currently expected.



### Plan

1. Inspect `test_query_with_partial_overlap` in `tests/unit/test_relevance_scorer.py` and identify which query words currently appear in the test chunk.

2. Review `RelevanceScorer.score()` in `rag/evaluator/relevance_scorer.py` to confirm that the score is calculated from the number of matching query tokens.

3. Change the test chunk so that it contains only some query words. For example, keep `Python` and `Django`, but remove `web` and `framework`.

4. Update the assertion to verify a real partial-overlap score. If two of four query words match, the expected score should be approximately `0.5`.

5. Run the focused test, the entire relevance-scorer test file, and the broader unit-test suite to confirm that the change works and does not introduce regressions.

Planned validation commands:

```bash
pytest tests/unit/test_relevance_scorer.py -k partial_overlap -q
pytest tests/unit/test_relevance_scorer.py -q
pytest tests/unit -q
```

### Inputs & outputs

The scorer takes these inputs:

* A query string.
* A list of chunks containing text.

Example query:

```text
Python Django web framework
```

Example corrected partial-overlap chunk:

```text
Python and Django are commonly used together
```

The corrected chunk contains two of the four query words:

```text
Python
Django
```

Expected calculation:

```text
2 matching query words / 4 total query words = 0.5
```

Expected output and behavior:

* `RelevanceScorer.score()` returns approximately `0.5`.
* The partial-overlap test passes.
* No-overlap tests continue returning `0.0`.
* Full-overlap tests continue returning `1.0`.
* The production implementation remains unchanged.
* Only the incorrect test fixture and possibly its assertion are modified.

### Risks & unknowns

* The replacement text in `tests/unit/test_relevance_scorer.py` could accidentally contain `web` or `framework`, making it a full-overlap fixture again.

* The tokenization logic in `rag/evaluator/relevance_scorer.py` may use simple whitespace splitting. Punctuation attached to a word could affect whether it matches.

* It is not yet confirmed whether maintainers prefer an exact assertion such as `pytest.approx(0.5)` or a range assertion such as `0.0 < score < 1.0`.

* Changing `RelevanceScorer.score()` could introduce regressions because the current implementation appears correct.

* The broader unit-test suite may contain unrelated failures that should not be confused with failures caused by this test change.

### Edge cases

* No query words appear in the chunk, producing `0.0`.

* All query words appear in the chunk, producing `1.0`.

* Only some query words appear in the chunk, producing a value between `0.0` and `1.0`.

* Query and chunk words use different capitalization, such as `Python` and `python`.

* The query is empty.

* The chunk list is empty.

* A chunk contains empty text.

* The query contains duplicate words.

* Multiple chunks are provided and their scores must be combined consistently.
