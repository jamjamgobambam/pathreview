## Solution plan

**Issue:** [Fix partial-overlap fixture in relevance scorer test](https://github.com/viswanathv4320/pathreview/issues/157)


### Understand

The test `test_query_with_partial_overlap` is intended to verify that a query with only partial overlap produces a relevance score between `0.3` and `0.9`.

The original test used this query:

```text
Python Django web framework
```

and this chunk:

```text
Django is a Python web framework for rapid development
```

All four meaningful query terms appear in the chunk, so the scorer correctly returns 1.0. The test data therefore represents full overlap, not partial overlap.

The expected behavior is for the fixture to contain only some of the query terms and produce a score in the middle range. The actual behavior was a score of 1.0 because the fixture contained complete overlap.

### Map
The main files involved are:

- tests/unit/test_relevance_scorer.py
- rag/evaluator/relevance_scorer.py

The implementation in rag/evaluator/relevance_scorer.py was reviewed to confirm how overlap is calculated, but no implementation change is expected.

The file that needs to be modified is:

- tests/unit/test_relevance_scorer.py

The specific test involved is:

- TestRelevanceScorer.test_query_with_partial_overlap

### Plan
1. Review the relevance scorer implementation to confirm how matching query terms are counted.
2. Replace the existing chunk text with text that contains only some of the query terms.
3. Run the individual partial-overlap test to confirm that the new fixture produces a middle-range score.
4. Run the full test_relevance_scorer.py test file to check for related failures.
5. Run the broader test suite and review the Git diff before committing the change.

### Inputs & outputs
The inputs are:

- A query string
- A list of chunks containing text

For this test, the query is:

```text
Python Django web framework
```

The revised chunk contains only partial overlap:

```text
Python is widely used for web applications
```

The expected output is:

- A float
- A score between 0.3 and 0.9
- A passing partial-overlap test

The fix changes only the test fixture and does not change the scorer's production behavior.

### Risks & unknowns
The replacement chunk must create genuine partial overlap according to the scorer's tokenization and matching logic.

A poorly chosen replacement could still produce full overlap, no overlap, or a score outside the expected range.

There is also a risk of unnecessarily changing the scorer implementation when the actual issue is only the inaccurate test fixture. To avoid expanding the scope, the implementation will remain unchanged unless broader tests reveal a separate defect.

There are no major unknowns remaining after reproducing the failure and reviewing the scorer logic.

### Edge cases
The scorer and its tests should handle these cases gracefully:

- Empty query
- Empty chunk list
- Chunk with empty text
- No matching query terms
- Partial overlap
- Complete overlap
- Repeated query terms
- Differences in capitalization or punctuation, depending on the current tokenization behavior
