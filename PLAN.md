# Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported —
https://github.com/ascherj/pathreview/issues/152

### Understand

**Expected:** A feedback claim that is genuinely backed by the retrieved
context should count toward the faithfulness score, regardless of how short the
claim is. Feedback made up of short, fully supported claims should score well
above 0.0.

**Actual:** `FaithfulnessChecker._is_supported` marks a claim supported only
when the claim and context share **at least two** meaningful (non-stopword)
tokens (`return len(meaningful_overlap) >= 2`). A short claim such as
"Knows Python." shares only one content word with a fully supporting context,
so it is always scored unsupported and such feedback scores 0.0.

**Root cause:** the hard `>= 2` overlap threshold, combined with a binary
all-or-nothing per-claim decision. Reproducing the bug surfaced three
contributing factors in the same file that the fix must account for:

1. **Threshold** — `>= 2` rejects any single-content-word claim.
2. **Tokenization** — tokens come from `str.split()` with no punctuation
   stripping, so `"Python,"` never matches `"python"`. This is why
   `test_multiple_context_chunks` fails even though the claim overlaps the
   context on Python/JavaScript/Docker.
3. **Claim extraction** — `_extract_claims` drops sentences of length `<= 10`
   chars, so `"Knows SQL"` (9 chars) is silently discarded before scoring.
4. **Binary scoring** — `test_partial_support_returns_middle_score` expects a
   *middle* score for a **single** claim that is only partially grounded. A
   binary supported/unsupported result can only ever yield 0.0 or 1.0 for one
   claim, so satisfying that test requires **graded per-claim support**, not
   just a lower threshold.

### Map

All changes are contained in the RAG evaluator and its test module:

- `rag/evaluator/faithfulness_checker.py` — the fix lives here:
  - `_is_supported` (lines ~66–88) → becomes a graded support score.
  - `check` (lines ~12–49) → averages per-claim scores.
  - `_extract_claims` (lines ~51–64) → revisit the `> 10` length filter.
  - a small tokenization/normalization helper (new) shared by claim + context.
- `tests/unit/test_faithfulness_checker.py` — the reproduction test
  (`test_short_single_token_claims_are_supported_issue_152`) plus the three
  existing failing tests define the target behavior.

No other modules import scoring internals, so blast radius is limited to this
package. (`agent/orchestrator.py` and the API consume the public `check()`
signature only, which will not change.)

### Plan

1. **Add a normalization helper** — a `_tokenize(text)` that lowercases, strips
   punctuation, splits on whitespace, and drops stop words. Use it for both the
   claim and the context so `"Python,"` and `"python"` match. Consider moving
   the stop-word set to a module-level constant.
2. **Make per-claim support graded** — replace the binary `_is_supported` with
   `_claim_support(claim, context) -> float` returning the fraction of the
   claim's meaningful tokens present in the context (0.0–1.0). A single-token
   claim that is present scores 1.0; a claim with one of two key terms scores
   ~0.5.
3. **Average per-claim scores in `check()`** — sum the graded per-claim scores
   and divide by the number of claims, keeping the 0.0–1.0 contract and the
   empty-input / no-claims guards.
4. **Revisit `_extract_claims` length filter** — lower/replace the `> 10` guard
   so short valid claims ("Knows SQL") survive, while still discarding empty or
   whitespace-only fragments.
5. **Tune against the full suite** — run
   `tests/unit/test_faithfulness_checker.py` and adjust the stop-word set /
   scoring until all faithfulness tests pass, including the #152 reproduction
   test and the three currently-failing tests, with no regressions elsewhere.

### Inputs & outputs

- **Input (unchanged):** `check(feedback: str, context_chunks: list[dict])`,
  where each chunk may carry a `"text"` string (possibly missing or `None`).
- **Output (unchanged type, changed values):** a `float` in `[0.0, 1.0]`. The
  behavioral change is that short, well-grounded claims now contribute positive
  support, and partially grounded claims yield intermediate scores rather than
  collapsing to 0.0.

### Risks & unknowns

- **Test tension between "fully supported" and "partial" (highest risk).**
  `test_feedback_fully_supported_by_context` asserts `score > 0.5` for a single
  claim, while `test_partial_support_returns_middle_score` asserts
  `0.2 < score < 0.8`. A naive "fraction of claim tokens found" model can drop a
  genuinely-supported claim below 0.5 (e.g. ~0.375 once neutral words like
  "developer"/"has"/"skills" dilute the denominator). I may need a curated
  stop-word list or to score over *content* terms only. This must be validated
  numerically against `tests/unit/test_faithfulness_checker.py`, not assumed.
- **Loosening support must not resurrect false positives** —
  `test_feedback_with_no_support_in_context` (Rust vs Python/JS) must still
  score `< 0.5`. Verify the graded model yields ~0 when there is no content
  overlap.
- **Changing `_extract_claims` may ripple** — `test_extract_claims`,
  `test_extract_claims_with_punctuation`, and `test_very_long_feedback` depend
  on current extraction behavior; the length-filter change must keep them green.
- **Purely lexical, not semantic** — the checker matches tokens, not meaning, so
  synonyms ("SQL" vs "database") still won't match. This matches the existing
  design and is out of scope for #152, but worth noting.

### Edge cases

- Single-content-word claims ("Knows Python.") — the core case; must score > 0.0.
- Punctuation-attached tokens ("Python," / "experience.") must normalize.
- Case differences ("PYTHON" vs "python") — already handled, keep handling.
- Claims consisting entirely of stop words — should not divide by zero; treat as
  neutral/unsupported without crashing.
- `context_chunks` with `"text": None` or a missing `"text"` key
  (`test_none_context_chunk_text`, `test_missing_text_key_in_chunk`) — must not
  raise.
- Empty feedback / empty context / both empty — keep returning 0.0.
- Very long feedback and very long context — must stay in `[0.0, 1.0]` and not
  blow up (claims already capped at 10).
