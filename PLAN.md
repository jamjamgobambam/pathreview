## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported — https://github.com/ascherj/pathreview/issues/152

### Understand

`_is_supported()` in `rag/evaluator/faithfulness_checker.py` marks a claim as supported only
if it shares at least 2 meaningful (non-stopword) tokens with the context. This threshold is
a fixed constant, not scaled to the claim's length. A claim with only one meaningful token
(e.g. "Knows Python.") can therefore never reach 2 overlapping tokens, no matter how well the
context supports it. Expected behavior: short, fully-supported claims should score as supported.
Actual behavior: they are always scored unsupported, dragging the overall faithfulness score
toward 0.0.

### Map

- `rag/evaluator/faithfulness_checker.py` — `_is_supported()` (the fix lives here)
- `tests/unit/test_faithfulness_checker.py` — 3 currently-failing tests define correct behavior;
  will also re-check the 18 currently-passing tests, especially `test_is_supported_without_keywords`
  and `test_minimum_overlap_required`, which encode the opposite boundary (claims that should
  correctly stay unsupported)

### Plan

1. Change the overlap threshold in `_is_supported()` from a fixed `>= 2` to a value scaled to
   the number of meaningful tokens in the claim itself (e.g. proportional with a floor of 1)
2. Run the full test file and confirm the 3 target tests now pass without breaking the 18
   currently-passing tests
3. Add a new unit test explicitly covering a single-meaningful-token claim (the exact case from
   the issue) so this regression can't silently return
4. Update the docstring for `_is_supported()` to describe the scaled-threshold behavior
5. Run `make check` (lint/format/typecheck) before opening the PR

### Inputs & outputs

Input: a claim string and a context string (already tokenized/lowercased inside the function).
Output: a boolean — whether the claim counts as "supported." No change to the public `check()`
signature or return type (still a float 0.0–1.0); only the internal decision rule changes.

### Risks & unknowns

- Loosening the threshold could make `_is_supported()` too permissive for longer claims,
  inflating faithfulness scores — need to verify `test_feedback_with_no_support_in_context`
  and `test_is_supported_without_keywords` still pass with plenty of margin, not just barely
- Unsure yet whether "proportional with a floor of 1" is the right ratio, or whether the
  course/rubric expects a different specific rule — will sanity-check against all existing
  tests rather than just the 3 named ones
- `test_minimum_overlap_required` asserts no specific boolean outcome (only
  `isinstance(supported, bool)`), but its comment documents the old fixed-threshold
  rule ("need at least 2 meaningful tokens"). Once the threshold scales with claim
  length, "Python expertise" vs "Python" (1 meaningful token, full overlap) may
  reasonably become supported=True. Need to decide in Week 9 whether to update this
  test's comment to reflect the new rule.
- `test_none_context_chunk_text` fails independently: `chunk.get("text", "")` only
  falls back when the "text" key is missing, not when its value is `None`, so
  `" ".join(...)` crashes in `check()` before `_is_supported()` is reached. This is
  issue #153's bug, a different code path — confirmed out of scope for this fix.

### Edge cases

- Claim with exactly one meaningful token (the reported case)
- Claim with zero meaningful tokens (all stopwords) — should not crash, should resolve to
  either always-unsupported or a defined default
- Very long claims with many meaningful tokens, to confirm the threshold still meaningfully
  filters unsupported ones (not accidentally becoming "always true")
- Claims ending in punctuation attached to the last token (e.g. "Knows Python.") —
  `.split()` doesn't strip trailing punctuation, so "python." never matches "python"
  in context even on identical words. Confirmed this independently while tracing
  `_is_supported()`; not part of issue #152's stated scope, so noting it here rather
  than fixing it in this PR, to keep the change focused.
