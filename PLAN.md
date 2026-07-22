# Solution Plan: Fix Short Claims Faithfulness Evaluation (#152)

**Issue:** Fix short claims faithfulness evaluation failure ([Issue #152](https://github.com/ascherj/pathreview/issues/152))

## Understand

- **Root Cause:** In `rag/evaluator/faithfulness_checker.py`, the claim extraction logic incorrectly parses or discards concise/short claims, treating valid multi-claim strings (e.g., `"Python expert. Knows Rust."`) as unsupported or missing. Additionally, when `context_chunks` contain `None` values for text, `context_text = " ".join(...)` raises an unhandled `TypeError`.
- **Expected vs. Actual:**
  - _Expected:_ Faithfulness score accurately reflects supported short claims, returning values between 0.0 and 1.0, and safely handling `None` context entries.
  - _Actual:_ Returns `0.0` unexpectedly for valid short claims and throws a `TypeError` when context text is `None`.

## Map

Files to touch/modify:

- `rag/evaluator/faithfulness_checker.py` — Update `check()` and `_extract_claims()` logic to handle `None` values and properly preserve/tokenize short claims.
- `tests/unit/test_faithfulness_checker.py` — Verify existing unit test cases pass and add edge case tests for short claims and `None` context chunks.

## Plan

1. **Handle `None` Values in Context Chunks:** Update string concatenation in `rag/evaluator/faithfulness_checker.py` to filter out or fallback `None` values to empty strings `""`.
2. **Refactor Claim Extraction (`_extract_claims`):** Ensure sentence/claim splitting does not discard short sentences or phrases that contain meaningful claim keywords.
3. **Verify Match Checks:** Check that the error handling, logging style, and typing match surrounding files in `rag/evaluator/`.
4. **Run Unit Tests:** Execute `pytest tests/unit/test_faithfulness_checker.py` to verify all 22 tests pass cleanly.

## Inputs & Outputs

- **Inputs:** `feedback` string (generated review) and `context_chunks` (list of dicts containing retrieved text).
- **Outputs:** A `float` score between `0.0` and `1.0` representing the ratio of faithful claims to retrieved context.

## Risks & Unknowns

- Refactoring the claim extraction function could inadvertently affect scoring thresholds for longer, multi-sentence feedback paragraphs.
- Need to ensure linter and type-checker (`make check`) pass without introducing any type errors in `rag/evaluator/`.

## Edge Cases

- `context_chunks` list containing `{"text": None}` or empty dicts.
- Extremely short claims consisting of 1–2 words (e.g., "Knows Rust.").
- Feedback strings with unusual punctuation or sentence boundaries.
