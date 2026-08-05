## Solution plan

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- The test fixture is incorrect, not the scorer. `test_query_with_partial_overlap` is
  meant to check that a chunk with only some overlapping query terms scores in a
  mid-range (0.3–0.9), but the fixture's chunk ("Django is a Python web framework for
  rapid development") actually contains all 4 query terms ("Python", "Django", "web",
  "framework"). The scorer correctly returns 1.0 for full coverage.
- Expected: chunk has partial keyword overlap with query, scorer returns a mid-range score.
- Actual: chunk has full overlap, scorer returns 1.0, test fails on `assert 0.3 < score < 0.9`.

### Map
Which files, functions, or modules are involved?
- `tests/unit/test_relevance_scorer.py` — specifically `test_query_with_partial_overlap`.
- No production code (`rag/evaluator/relevance_scorer.py`) needs to change; the scorer
  behavior is correct.

### Plan
What are the steps to fix this issue?
1. Rewrite the chunk text in `test_query_with_partial_overlap` so it overlaps on only
   some of the 4 query terms (e.g. just "Python" and "web") instead of all 4.
2. Confirm the assertion range (`0.3 < score < 0.9`) still makes sense for the new partial overlap — adjust if needed.
3. Run `pytest tests/unit/test_relevance_scorer.py -q` to confirm the test now passes.
4. Check whether the same query/chunk pair is reused in other tests in the file, to
   avoid breaking anything else.
5. Commit the fix, referencing the reproduction commit.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- Input: the `query` string and `chunks` list defined inside the test function
  (self-contained, no external input).
- Output: `scorer.score(query, chunks)` should return a float in the range 0.3–0.9,
  and the test should pass with no AssertionError when run via pytest.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- Low risk overall — this is a one-line data change in a test fixture, not production code.
- Main unknown: what "partial overlap" ratio the scorer's design intends to test (e.g.
  whether 50% term overlap should score close to 0.5, or non-linearly). I'll pick a
  chunk overlap that's unambiguously partial (not 0%, not 100%) rather than aim for an
  exact target score.

### Edge cases
What inputs or states should your fix handle gracefully?
- New chunk text shouldn't accidentally overlap 0 query terms (that tests "no overlap,"
  not "partial overlap") or all 4 terms again (reintroducing the original bug).
- Confirm the chunk/query pair isn't reused elsewhere in the file in a way that would
  be affected by this change.