## Solution plan

**Issue:** 

**Issue link:** (https://github.com/ascherj/pathreview/issues/157)

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

### Understand
The test asserts that a "partial overlap" query scores below 0.9, but the fixture chunk
actually contains all four terms from the query "Python Django web framework" — i.e. full
coverage, not partial. The relevance scorer is behaving correctly: it returns 1.0 for full
keyword coverage. The test's expectation (`score < 0.9`) is wrong given the fixture as written.

- **Expected behavior:** A chunk with only some of the query terms present should score below 0.9.

- **Actual behavior:** The chunk contains every query term, so the scorer correctly returns 1.0,
  and the test fails on `assert 1.0 < 0.9`.
- **Root cause:** Fixture design, not scorer logic.

### Map
- `tests/unit/test_relevance_scorer.py` — contains `test_query_with_partial_overlap` and its
  fixture chunk. This is the only file I expect to touch.
- No changes to the scorer source itself; its behavior is already correct.

### Plan
1. Locate `test_query_with_partial_overlap` and inspect the current query string and chunk fixture.
2. Rewrite the chunk so it contains only a subset of the query terms (e.g. drop "Django" and
   "framework" from the chunk text, keeping "Python" and "web"), so overlap is genuinely partial.
3. Confirm the expected score threshold (`< 0.9`) still makes sense for the new partial-overlap
   fixture — adjust the assertion value if needed based on actual scorer output.
4. Run `pytest tests/unit/test_relevance_scorer.py -q` to confirm the test now passes.
5. Commit the fix separately from the earlier reproduction commit.

### Inputs & outputs
- **Input:** The fixture's chunk text and query string inside the test function.
- **Output:** An updated chunk string with genuine partial term overlap, and a passing test that
  correctly validates partial-overlap scoring behavior (rather than accidentally testing full
  coverage).

### Risks & unknowns
- Unsure of the scorer's exact scoring curve — need to check what score a genuinely partial
  overlap actually produces, in case the `< 0.9` threshold needs to move too (e.g. if partial
  overlap only drops the score to 0.92, the assertion itself may need adjusting, not just the fixture).
- Small risk of accidentally creating a *new* full-overlap or *zero*-overlap fixture if term
  selection isn't careful — need to verify the new chunk isn't degenerate in the other direction.

### Edge cases
- Chunk with exactly one overlapping term out of four (minimal partial overlap — good sanity check
  that the fix produces a real gradient, not just "not 1.0").