# Plan: Fix faithfulness checker crash for None context text

## Goal
Handle `None` values in context chunk text so the faithfulness checker does not crash when a retrieved chunk contains `{"text": None}`.

## Approach
1. Inspect the faithfulness checker implementation and the existing unit tests for this edge case.
2. Update the checker to normalize missing or `None` chunk text values to an empty string before building the combined context string.
3. Add or confirm a regression test that exercises a chunk with `text: None` and verifies the checker returns a valid float score instead of raising.
4. Run the relevant unit tests to verify the fix.

## Files to touch
- rag/evaluator/faithfulness_checker.py
- tests/unit/test_faithfulness_checker.py

## Risks and unknowns
- The checker currently relies on simple keyword overlap, so the fix should stay narrowly scoped to input normalization.
- If the project uses additional evaluator paths, they may need the same normalization rule to stay consistent.
- Test environment setup may require installing dependencies before running the targeted pytest case.
