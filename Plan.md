## Solution plan
 
**Issue:** Faithfulness checker can never mark short claims as supported #152 
### Understand
`_is_supported(claim: str, context: str) -> bool`
 
```python
claim_tokens = set(claim.lower().split())
context_tokens = set(context.lower().split())
overlap = claim_tokens & context_tokens
meaningful_overlap = overlap - stop_words  
return len(meaningful_overlap) >= 2
```
 
Short factual claims (e.g. "Knows Python.") often only share **one** meaningful
token with a fully supporting context (e.g. "python expert" → shared token:
"python"), so they always fail the hardcoded `>= 2` threshold and get scored
as unsupported.
 
- Expected: a claim like "Knows Python." checked against context
  "python expert" should be scored as supported 
- Actual: `check()` returns 0.0 because every claim in the example
  only overlaps by a single token, so `_is_supported()` returns
  `False`.
- Root cause: the hardcoded `>= 2` token-overlap threshold doesn't scale down
  for short claims. it implicitly assumes claims will always contain at
  least 2 meaningful tokens, which isn't true for terse, single-fact statements.
- Related wrinkle to verify during reproduction: tokenization is a plain
  `.split()` with no punctuation stripping, so a claim ending in a period
  (e.g. `"python."`) may not even match a context token like `"python"`
  (no trailing punctuation). Need to check whether claims are pre-cleaned
  before reaching `_is_supported()`, since the issue's repro implies the
  overlap of "python" does register
### Map
Files/functions
- `rag/evaluator/faithfulness_checker.py`
  - `_is_supported(claim: str, context: str) -> bool` 
    a static, single claim pair check with a hardcoded stopword
    literal and a hardcoded `>= 2` threshold. replace the fixed
    threshold with logic that scales relative to the number of meaningful
    tokens in the claim.
  - Whatever caller loops over claims and context chunks and calls
    `_is_supported()` per pair. I need to confirm it doesn't have its own length-dependent logic.
- `tests/unit/test_faithfulness_checker.py`
  - `test_partial_support_returns_middle_score`
  - `test_multiple_context_chunks`
  - `test_multiple_claims_varying_support`
  - Plus a new regression test for the short-claim case from the issue
    (e.g. `test_short_claim_single_token_overlap_scores_supported`).
### Plan
1. Reproduce the bug locally and confirm the three related tests fail for
   the same underlying reason (the `>= 2` threshold), not for unrelated bugs.
2. Read `_is_supported()` in full and enumerate its current parameters
   (stopword list, tokenization method, threshold constant) to understand
   what "non-stopword token" means in this codebase and whether the
   stopword list itself needs adjusting too.
3. Redesign the support-decision logic so it scales with claim length.
   Should require overlap of *all* meaningful tokens for claims with <= 2 of
   them, and keep the `>= 2` rule for longer claims. Decide
   between an absolute vs. ratio-based threshold and document the tradeoff.
4. Update `_is_supported()` with the new logic,
   keeping the existing multi-chunk context matching behavior intact.
5. Run the full test suite for this file, confirm the three named tests
   and the new short-claim test all pass, and check for regressions in
   longer-claim cases
### Inputs & outputs
- **Input:** a claim string (e.g. `"Knows Python. Knows SQL."`, split into
  individual claims) and a list of context chunks (dicts with a `text` key).
- **Output:** `check()` returns a faithfulness score (float, 0.0–1.0)
  representing the fraction of claims supported by the context;
  `_is_supported()` returns a bool per claim/context pair.
- After the fix: short, fully-supported claims should no longer be
  automatically scored as unsupported — the output score should reflect
  actual support, not claim length.
### Risks & unknowns
- Loosening the threshold for short claims could make the checker too
  permissive — e.g. a 1-token claim like "Python." might match almost any
  context mentioning Python out of context. Need to test edge cases where
  a short claim's single token appears in an unrelated context.
- The stopword list in `_is_supported()` is a small hardcoded literal
  (`{'a','an','the','is','are','was','were','be','been','and','or','but',
  'in','of','to','for','that'}`) — it's minimal and may not cover every
  filler word, so some claims could have *zero* meaningful tokens even
  before this bug's threshold applies. Need to check for that edge case.
- Tokenization is plain `.split()` with no punctuation stripping — a
  trailing period on the last word of a claim (e.g. `"python."`) could
  prevent it from matching a clean context token (`"python"`). Need to
  confirm where/if claims get punctuation-stripped before reaching
  `_is_supported()`, since fixing the threshold alone won't help if this
  tokenization issue is also in play for the reported examples.
- Changing `_is_supported()`'s behavior could affect other tests not listed
  in the issue, need to run the full test file,
  not just the three named tests.
- Not yet sure whether `_is_supported()` is used elsewhere in the codebase
  (e.g. other evaluators) need to grep for callers before changing its
  signature or return semantics, since it appears to be a `@staticmethod`-style
  function (no `self` in its signature) that could be reused.
### Edge cases
- Claim with exactly 1 meaningful (non-stopword) token, fully supported by
  context (the reported bug case).
- Claim with 0 meaningful tokens should this be
  "unsupported" by definition, or "not evaluable"?
- Claim with 1 meaningful token that does *not* appear in any context chunk
  (should correctly stay unsupported — guards against over-loosening).
- Multiple context chunks where a short claim's token appears in one chunk
  but not others (`test_multiple_context_chunks`).
- Mixed batch of short and long claims with varying support levels
  (`test_multiple_claims_varying_support`, `test_partial_support_returns_middle_score`).
 

