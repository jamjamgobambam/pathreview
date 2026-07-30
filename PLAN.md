## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported — https://github.com/ascherj/pathreview/issues/152

### Understand

The root cause is the faithfulness checker heuristic in `rag/evaluator/faithfulness_checker.py`. It currently treats support as requiring at least two meaningful token overlaps between a claim and the retrieved context.

Expected behavior: short factual claims such as "The candidate knows Python." should be considered supported when the context contains the same key term.
Actual behavior: short claims with only one strong keyword match are marked unsupported, causing valid feedback to score incorrectly.

### Map

Files/modules involved:

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`
- `JOURNAL.md` (reproduction documentation)
- `PLAN.md`

### Plan

1. Add regression coverage for the short-claim issue in `tests/unit/test_faithfulness_checker.py`.
2. Update `_extract_claims()` to split compound sentences into shorter claim segments and retain short factual statements.
3. Update `_is_supported()` to use regex tokenization, filter stop words, and allow a single strong token overlap for short claim cores.
4. Document the reproduction and fix approach in `JOURNAL.md` and verify with direct execution and compilation.

### Inputs & outputs

Input: feedback text and a list of retrieved context chunks.
Output: a faithfulness score that correctly reflects supported short claims, plus regression tests that capture the bug.

### Risks & unknowns

- The new heuristic could become too permissive for generic short claims.
- Compound claim splitting may over-segment some natural language feedback.
- Need to ensure `None` or missing context text remains handled gracefully.

### Edge cases

- Short factual claims with a single meaningful token
- Compound claims connected by commas, "and", or "or"
- Claims containing only stop words or generic filler terms
- Context chunks with missing or `None` text
- Very long feedback or context inputs
