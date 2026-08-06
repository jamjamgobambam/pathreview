## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported (#152) — https://github.com/ascherj/pathreview/issues/152

### Understand
Expected: short, factual claims that are genuinely backed by the retrieved context
(e.g. "Knows Python.") should be scored as supported. Actual: they are always
scored unsupported, so feedback made of short accurate sentences gets a
faithfulness score of 0.0.

Root cause is two compounding bugs in `rag/evaluator/faithfulness_checker.py`:

1. `_extract_claims()` filters out any sentence with `len(s.strip()) <= 10`
   before it's ever scored. Reproduced: `_extract_claims("Knows Python. Knows SQL.")`
   returns only `["Knows Python"]` — "Knows SQL" (9 chars) is silently dropped.
2. `_is_supported()` requires at least 2 non-stopword tokens to overlap between
   a claim and the context, with no regard for how many meaningful tokens the
   claim even has. A claim like "Knows Python" has exactly one meaningful token
   ("python"), so it can never reach the threshold of 2 — even when the context
   is "python expert" and fully supports it.

Reproduced with the issue's exact script:
`FaithfulnessChecker().check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])`
returns `0.0` (see commit documenting the reproduction).

### Map
Files/functions involved:
- `rag/evaluator/faithfulness_checker.py` — `_extract_claims()` (length filter,
  line ~64-69) and `_is_supported()` (overlap threshold, line ~71-113) are the
  two functions I expect to change. `check()` itself likely stays the same.
- `tests/unit/test_faithfulness_checker.py` — 3 tests named in the issue
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`) currently fail because of this bug and
  should pass after the fix. Several other tests
  (`test_feedback_with_no_support_in_context`, `test_is_supported_without_keywords`,
  `test_minimum_overlap_required`) depend on *some* minimum bar still existing and
  must keep passing so the fix doesn't just remove all filtering.
- No other module imports `_extract_claims` or `_is_supported` directly — both
  are internal helpers only reached through `check()` — so the blast radius is
  contained to this one file and its test file.

### Plan
1. Lower (or remove) the fixed `len(s.strip()) > 10` filter in `_extract_claims()`
   so short factual sentences aren't discarded before they're scored, while still
   filtering out truly empty/junk fragments.
2. Replace the fixed `>= 2` meaningful-token-overlap threshold in `_is_supported()`
   with a threshold that scales with the claim's own meaningful-token count (e.g.
   require overlap proportional to claim length, with a minimum of 1), so a
   single strong match can support a short claim without loosening the bar for
   longer claims.
3. Re-run `tests/unit/test_faithfulness_checker.py` and confirm all 3 named
   failing tests pass without breaking any of the 18 currently-passing tests,
   paying particular attention to the "no support" tests.
4. Add a regression test that reproduces the issue's exact script (two short,
   fully-supported claims) to lock in the fix and prevent this from regressing.
5. Run `make check && make test-unit` before opening the PR, per CONTRIBUTING.md.

### Inputs & outputs
Input: `feedback` (a string of one or more sentences) and `context_chunks` (a
list of dicts with a `"text"` key), passed to `FaithfulnessChecker.check()`.
Output: a float in `[0.0, 1.0]` — the ratio of claims judged supported. The fix
changes how that ratio is computed for short claims; the method signature and
return type are unchanged.

### Risks & unknowns
- Loosening the overlap threshold too far could make `test_feedback_with_no_support_in_context`
  or `test_is_supported_without_keywords` start passing when they shouldn't
  (false positives) — need to verify fully-unsupported cases still score low
  after the change.
- The issue doesn't prescribe an exact scaling formula for the overlap
  threshold; I'll need to pick something defensible (e.g. overlap ratio vs.
  claim token count) and be ready to explain the reasoning in the PR, or ask in
  Slack/office hours if the existing tests don't sufficiently pin down intended
  behavior.
- Changing the `_extract_claims()` length filter could change claim counts for
  longer, existing feedback too — need to check `test_extract_claims_with_punctuation`
  and `test_very_long_feedback` still behave sensibly, not just the short-claim cases.
- `test_none_context_chunk_text` currently fails independently of this issue
  (`TypeError` when a chunk's `"text"` value is explicitly `None`, since
  `chunk.get("text", "")` only applies its default when the key is *missing*,
  not when the value is `None`). This is in the same file/function I'm already
  touching (`check()`'s context-concatenation step) but is not part of #152's
  described scope — I'll flag it explicitly in the PR rather than silently
  fixing or ignoring it.

### Edge cases
- A claim with exactly one meaningful token that's a strong exact match (e.g.
  "Knows Python" vs. "python expert") — should be supported.
- A claim with zero meaningful tokens after stopword filtering (e.g. all
  stopwords) — should not crash and should be treated as unsupported, not as a
  divide-by-zero or similar.
- Very short claims that are pure noise (e.g. "It is") — loosening the length
  filter shouldn't let junk fragments through as scoreable claims.
- `context_chunks` with an explicit `None` text value — currently crashes with
  a `TypeError`; decide whether to fix as part of this PR or call out as a
  follow-up (see Risks above).
- Feedback with a mix of short and long claims with varying support — the
  score should still reflect the correct ratio (this is what
  `test_multiple_claims_varying_support` checks).
