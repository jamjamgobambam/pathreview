# PLAN.md — Issue #152: Faithfulness checker can never mark short claims as supported

## Problem

`FaithfulnessChecker._is_supported()` in `rag/evaluator/faithfulness_checker.py`
requires a flat `>= 2` meaningful (non-stop-word) token overlap between a claim
and the retrieved context before marking the claim as supported. Short claims
(2-3 content words) can only ever satisfy this if every one of those words
appears verbatim in the context — any paraphrase, tense change, or synonym
drops the overlap below 2 and the claim is wrongly marked unsupported.
Reproduced in `tests/unit/test_faithfulness_checker.py::test_short_claim_with_partial_paraphrase_should_be_supported`
(commit a49fe21): claim "Good communicator" vs. context "Excellent
communicator with clients and stakeholders" overlaps on only "communicator"
(1 token) and fails, despite being clearly supported.

## Files to change

- `rag/evaluator/faithfulness_checker.py` — the actual fix, in `_is_supported()`.
- `tests/unit/test_faithfulness_checker.py` — flip the reproduction test to
  assert `True`; update `test_minimum_overlap_required`'s expected value
  (see Risks below); add new tests for the scaling rule's edge cases.

## Fix approach

Replace the flat threshold with one that scales to the claim's own meaningful
token count, requiring a majority overlap instead of a fixed count of 2:

```python
claim_meaningful = claim_tokens - stop_words
required_overlap = max(1, (len(claim_meaningful) + 1) // 2)  # majority, rounded up
return len(meaningful_overlap) >= required_overlap
```

- Short claims (1-2 meaningful tokens): `required_overlap = 1` — one real
  keyword match is enough. Fixes the reported bug.
- Longer claims (4+ meaningful tokens): `required_overlap` grows past 2, so
  vague or padded claims still need real evidence, not a single lucky match.
- Zero-meaningful-token claims (all stop words): `required_overlap` floors
  at 1, so an empty-content claim can never spuriously pass.

## Sub-tasks (in order)

1. Add a `claim_tokens - stop_words` computation in `_is_supported()` to get
   the claim's own meaningful token count (context side already computes
   `meaningful_overlap`, but currently nothing measures the claim's total).
2. Replace `return len(meaningful_overlap) >= 2` with the scaled
   `required_overlap` rule above.
3. Update `test_minimum_overlap_required` — "Python expertise" vs. "Python"
   is a 2-meaningful-token claim, so under the new rule
   `required_overlap = 1` and it now passes with 1 overlap. Change its
   assertion from `False` to `True` and update the docstring/comment to
   explain why.
4. Flip `test_short_claim_with_partial_paraphrase_should_be_supported`'s
   assertion comment (it already asserts `True`; just remove the "currently
   fails" note once it passes).
5. Add new unit tests for the rule's edge cases:
   - A single-meaningful-token claim (e.g. "Python.") that matches exactly
     one word in context — should pass.
   - A single-meaningful-token claim that matches nothing — should fail.
   - An all-stop-word claim (if reachable — `_extract_claims` filters by
     length so check whether this is actually reachable in practice) —
     should not spuriously pass.
   - A long, vague claim (4+ tokens) with only 1 real overlap — should still
     fail, confirming the stricter bar is preserved for longer claims.
6. Run `make test-unit` and confirm no other test in the suite (e.g.
   `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
   `test_multiple_claims_varying_support` — currently failing for unrelated
   reasons per the Week 8 reproduction) changes status unexpectedly because
   of this change; note any that do.
7. Run `make check` (lint + format + typecheck) before opening the PR.

## Risks and edge cases

- **`test_minimum_overlap_required` intentionally flips.** This is expected,
  not a regression — it currently documents the *buggy* behavior. Needs a
  clear commit message explaining why its assertion changed.
- **Interaction with issue #153** (`text: None` crash) — that bug currently
  makes `test_none_context_chunk_text` fail before `_is_supported()` is even
  reached. Not in scope for #152, but worth noting so the PR doesn't
  accidentally get blamed for that failure.
- **Over-leniency for medium-length claims.** The `(n+1)//2` majority rule is
  a judgment call — a 3-token claim now only needs 2 matches (same as
  before), but a 2-token claim needs only 1 (down from 2). Need to sanity
  check this doesn't make faithfulness scores too generous in the
  `test_score_never_returns_hardcoded_value`-style checks that expect scores
  to meaningfully vary.
- **Stop-word filtering is still naive.** `test_common_words_filtered_in_overlap`
  already documents that opposite-meaning claims ("well documented" vs.
  "poorly documented") can pass due to shared non-opposite tokens. The
  scaling fix doesn't address this — it's a separate, deeper limitation of
  keyword-overlap matching, explicitly out of scope for #152.

## Testing strategy

- Unit tests only (`tests/unit/test_faithfulness_checker.py`) — this is a
  pure-function change with no DB/API/frontend surface, so `make test-unit`
  is sufficient; no integration test changes expected.
