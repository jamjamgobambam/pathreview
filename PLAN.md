## Solution plan

**Issue:** [Relevance scorer "partial overlap" test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Understand
`test_query_with_partial_overlap` in `tests/unit/test_relevance_scorer.py` is meant to exercise a case where a chunk only partially covers the query's keywords. Its query is `"Python Django web framework"` (4 tokens) against the chunk `"Django is a Python web framework for rapid development"`, which contains all 4 of those tokens. `RelevanceScorer.score()` computes overlap as `len(query_tokens & chunk_tokens) / len(query_tokens)`, so full coverage correctly yields `1.0`. The test then asserts `0.3 < score < 0.9`, which is wrong for a fixture with 100% coverage — expected behavior is `1.0`, actual is also `1.0`, but the assertion range excludes it. This isn't a scorer bug; it's a bad fixture that never actually tests partial overlap.

### Map
- `tests/unit/test_relevance_scorer.py` — `test_query_with_partial_overlap` (lines ~47-60): the fixture and assertion to rewrite.
- `rag/evaluator/relevance_scorer.py` — `RelevanceScorer.score()` and `_tokenize()`: read-only reference to confirm the new fixture produces a genuinely partial overlap ratio; no production code changes expected.

### Plan
1. ✅ Rewrite the chunk text so it contains only some of the query's tokens — changed it to "Python is a popular language for many web applications", which keeps "python" and "web" but drops "django" and "framework".
2. ✅ Manually compute the expected overlap ratio for the new fixture — 2 matching tokens / 4 query tokens = 0.5, comfortably inside `0.3 < score < 0.9`.
3. ✅ Assertion bounds needed no changes — the original `0.3 < score < 0.9` already describes a genuine partial-overlap case once the fixture is honest.
4. ✅ Ran `pytest tests/unit/test_relevance_scorer.py -q` — all 19 tests pass, including the rewritten one.
5. ✅ Re-read the docstring ("Test query with partial overlap returns score between 0 and 1.") — still accurate, no changes needed.

### Inputs & outputs
- Input: the `query` string and `chunks` list literals inside the test function body (no function signatures change).
- Output: the test still calls `scorer.score(query, chunks)` and asserts on the returned float; only the fixture data and assertion bounds change. No changes to `RelevanceScorer` itself — its behavior is already correct.

### Risks & unknowns
- Risk: picking a new chunk text where tokenization (`_tokenize` just lowercases and splits on whitespace, no punctuation stripping) causes unexpected token boundaries — need to verify tokens split cleanly, no attached punctuation inflating/deflating overlap.
- Risk: choosing bounds too tight (e.g. exact equality) makes the test brittle to minor future changes in `RelevanceScorer.score()`; keep a reasonable range like the original style (`0.x < score < 0.y`).
- Unknown: whether other tests (`test_score_ranges_from_zero_to_one`, `test_multiple_keyword_matches`) rely on similar coverage math that should also be double-checked for the same "not actually partial" mistake — worth a quick scan even though only issue #157 is in scope.

### Edge cases
- Chunk containing zero of the query's tokens should not be used (that's `test_query_with_zero_keyword_overlap`'s job, not this test's).
- Chunk containing exactly 1 of 4 query tokens vs. 2 of 4 — pick whichever gives a score comfortably inside the asserted range so the test isn't flaky against float division (e.g. avoid boundary values like exactly 0.3 or 0.9).
