## Solution plan

**Issue:** Relevance scorer "partial overlap" test fixture actually has full query overlap: https://github.com/ascherj/pathreview/issues/157

### Understand
The issue isn't with the relevance scorer itself—it's with the test data. The test `test_query_with_partial_overlap` is supposed to check that the scorer returns a score somewhere in the middle (between 0.3 and 0.9) when a query and a document chunk only partially match. However, the current test uses the query "Python Django web framework" and the chunk "Django is a Python web framework for rapid development." Since all four query words appear in the chunk, the scorer correctly returns a perfect score of 1.0. The test fails because the fixture represents a full match instead of a partial one. The fix is to update the test data so only some of the query terms appear in the chunk, which should naturally produce a score in the expected range.

### Map
- `tests/unit/test_relevance_scorer.py` — contains the failing test and the fixture that needs to be updated. This should be the only file that requires changes.
- `rag/evaluator/relevance_scorer.py` — contains the `RelevanceScorer.score()` implementation. I don't expect to modify this file, but I'll review it to understand exactly how overlap is calculated before creating a new test fixture.

### Plan
1. Read through `RelevanceScorer.score()` to understand how it calculates overlap and what contributes to the final score.
2. Create a new query and chunk where only some of the query terms overlap (for example, 2 out of 4 words).
3. Verify that the new fixture produces a score between 0.3 and 0.9, either manually or with a quick script.
4. Replace the existing fixture in `test_query_with_partial_overlap` with the new query/chunk pair.
5. Run `pytest tests/unit/test_relevance_scorer.py -q` to confirm the test passes, then run the full test suite to make sure nothing else is affected.

### Inputs & outputs
**Input:** A query string and a list of document chunk dictionaries (each containing a `text` field) passed into `scorer.score(query, chunks)`.
**Output:** A relevance score between 0.0 and 1.0. For this specific test, the updated fixture should produce a score strictly between 0.3 and 0.9 to represent a true partial match.

### Risks & unknowns
- I don't know the exact scoring formula yet. If the scorer does more than simple word overlap (such as weighting terms or filtering stop words), I may need to adjust the fixture until it lands in the expected range.
- I want to avoid creating a test that's too close to either boundary (0.3 or 0.9), since that could make it more fragile if the scoring logic changes slightly in the future.
- I'll also confirm that this fixture isn't shared with any other tests in the file before making changes.

### Edge cases
- Make sure query words aren't accidentally matching as substrings (for example, "Python" matching "Pythonic"), since that could affect the score unexpectedly.
- Check whether matching is case-sensitive so the fixture behaves as intended.
- Empty or whitespace-only chunks aren't part of this issue, but it's worth keeping in mind that the scorer should already handle those cases correctly.