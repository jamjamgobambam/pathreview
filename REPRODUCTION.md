# Issue #157 Reproduction

## Environment

- Baseline: upstream `main` before the Issue #157 fixture fix
- Python: 3.11
- Test file: `tests/unit/test_relevance_scorer.py`
- Implementation: `rag/evaluator/relevance_scorer.py`

## Reproduction command

```bash
pytest tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap -q
```

## Pre-fix observed behavior

Before this fix, the test failed at `assert 0.3 < score < 0.9` because `score`
was `1.0`. The query was `Python Django web framework`, and the previous fixture
text was
`Django is a Python web framework for rapid development`. All four query
tokens occurred in that fixture text, so the scorer correctly calculated full
keyword coverage rather than partial overlap.

## Expected behavior

The fixture should omit at least one query token while retaining enough shared
tokens to produce a score strictly between `0.3` and `0.9`. The production
scoring implementation should remain unchanged because its current result is
correct for the supplied input.

## Scope

The defect is in the `test_query_with_partial_overlap` fixture in
`tests/unit/test_relevance_scorer.py`. It is not a defect in
`RelevanceScorer.score()` in `rag/evaluator/relevance_scorer.py`.
