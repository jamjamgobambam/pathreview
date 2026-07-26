# Solution Plan

**Issue:**
Faithfulness checker can never mark short claims as supported (#152)

## Understand

The faithfulness checker currently requires at least two overlapping meaningful tokens between a claim and the retrieved context. Very short factual claims often contain only one important keyword, causing correctly supported claims to be marked unsupported.

Expected:
Short factual claims should be marked as supported when the context clearly contains the same concept.

Actual:
Claims like "Knows Python." always receive an unsupported score even when the context contains "Python expert."

---

## Map

Files involved:

- rag/evaluator/faithfulness_checker.py
- tests/unit/test_faithfulness_checker.py

Functions involved:

- FaithfulnessChecker.check()
- FaithfulnessChecker._is_supported()

---

## Plan

1. Reproduce the failing tests.
2. Handle None values safely when building the context text.
3. Improve token matching for short factual claims.
4. Keep existing behavior for unsupported claims.
5. Run all unit tests to confirm the fix.

---

## Inputs & Outputs

Input:

- feedback string
- context chunks

Output:

- faithfulness score between 0.0 and 1.0

---

## Risks & Unknowns

Changing the overlap logic may accidentally increase false positives.

Need to preserve behavior for unsupported claims while improving short supported claims.

---

## Edge Cases

- Empty feedback
- Empty context
- None context text
- Missing text key
- Single-word claims
- Multiple context chunks