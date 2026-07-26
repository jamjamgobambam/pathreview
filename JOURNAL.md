# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method in `rag/evaluator/faithfulness_checker.py`
builds a single context string by joining `chunk.get("text", "")` for every retrieved
chunk. Because `dict.get()` only applies its default when the key is *missing*, a chunk
that explicitly stores `"text": None` returns `None` instead of `""`, and the following
`" ".join(...)` raises a `TypeError`. As a result, any RAG result that contains a chunk
with a null `text` field crashes the faithfulness evaluation instead of returning a score.
A successful fix should coerce `None` (and missing keys) to an empty string before joining,
so malformed chunks are handled gracefully and the related unit test
`test_none_context_chunk_text` passes.

**Branch name:** fix/153-faithfulness-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes / "Is this right for me?" checklist

- **Tier label:** Tier 1 / `good first issue` — explicitly recommended for first-time contributors.
- **Understand the problem:** Yes. The bug is a straightforward `None` handling issue in `str.join()`.
- **Can I reproduce it?** Yes. Running `test_none_context_chunk_text` fails with the exact `TypeError` described in the issue.
- **Scope is limited:** Yes. The fix is localized to one file (`rag/evaluator/faithfulness_checker.py`) and one expression, plus formatting.
- **Existing tests cover it:** Yes. `tests/unit/test_faithfulness_checker.py` already includes `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`.
- **No external API keys needed:** The test runs with `LLM_PROVIDER=mock` and does not require OpenAI or GitHub tokens.
- **Subsystem I can explain:** `rag/evaluator` — the faithfulness scoring step in the RAG pipeline.
- **Realistic to finish in a week:** Yes. The fix and verification took a single session; remaining work is testing, lint, and PR.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/esfahani-moein/codepath_pathreview/commit/3fdf3b9

**Reproduction summary:**
Created `reproduce_issue_153.py` which simulates the original buggy expression
`" ".join([chunk.get("text", "") for chunk in context_chunks])` with input
`[{"text": None}]` and confirms it raises `TypeError: sequence item 0: expected str
instance, NoneType found`. The script then runs the fixed `FaithfulnessChecker.check()`
method on the same input and confirms it returns a valid score (0.0) without crashing.

**PLAN.md link:** https://github.com/esfahani-moein/codepath_pathreview/blob/fix/153-faithfulness-none-text/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
Three pre-existing unit test failures (`test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`) are unrelated to
this issue — they stem from the stop-word filtering logic in `_is_supported()`. These
should not block the PR for #153 but may need separate issues filed.
