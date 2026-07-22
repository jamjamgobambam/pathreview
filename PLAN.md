## Solution plan

**Issue:** [Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

### Understand

`FaithfulnessChecker.check()` splits generated feedback into claims, checks each
claim against the retrieved context via `_is_supported()`, and scores the
feedback as `supported_count / total_claims`. Two bugs in
`rag/evaluator/faithfulness_checker.py` combine to make short claims
unscoreable:

1. `_extract_claims()` discards any claim of 10 characters or fewer before it
   ever reaches scoring (`len(s.strip()) > 10`). A claim like `"Knows SQL"`
   (9 characters) never becomes a scoreable claim at all.
2. `_is_supported()` requires a fixed minimum of **2** overlapping
   non-stopword tokens between the claim and the context
   (`len(meaningful_overlap) >= 2`). A claim with only one or two meaningful
   words (e.g. `"Knows Python"`) can never clear this bar, even when its one
   substantive word ("Python") is fully present in the context.

**Expected:** `checker.check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])` → `1.0` (both claims are clearly backed by context).
**Actual:** → `0.0` (both claims marked unsupported).

The root cause is that the checker conflates "claim is short" with "claim is
unsupported" — the fixed absolute thresholds (10-char length floor, 2-token
overlap floor) don't scale down for short claims, so short-but-true claims
get penalized purely for their length rather than their accuracy.

### Map

Files touched:
- `rag/evaluator/faithfulness_checker.py` — `_extract_claims()` and
  `_is_supported()`, the two methods with the length/overlap thresholds.
- `tests/unit/test_faithfulness_checker.py` — existing test suite; three
  tests already encode the bug (`test_partial_support_returns_middle_score`,
  `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) and
  need a new regression test for the issue's own example.

Not touched: `rag/evaluator/eval_suite.py` and `scripts/run_evals.py`, which
call `FaithfulnessChecker` but only consume the final float score — no
change to the public `check()` signature or return type, so callers are
unaffected.

### Plan

1. Lower `_extract_claims()`'s minimum claim length so short factual claims
   (e.g. "Knows SQL") aren't dropped before scoring, and split claims further
   on commas/"and" so compound sentences ("X, Y, and Z") yield one claim per
   fact instead of one long claim with a diluted token overlap.
2. Replace `_is_supported()`'s fixed `>= 2` overlap-token requirement with a
   check anchored on capitalized key terms (technology/proper nouns like
   "Python", "SQL", "Docker") — require just one such term to appear in the
   context, since a single specific match is a strong signal regardless of
   how short the claim is.
3. Add a non-stopword fallback in `_is_supported()` for claims with no
   capitalized terms, so the method doesn't silently regress to "always
   unsupported" for lowercase-only claims.
4. Add a regression test using the issue's exact example
   (`"Knows Python. Knows SQL."` against `"python expert"` / `"sql expert"`
   → `1.0`), and verify the three already-failing tests named in the issue
   now pass.
5. Run `make check` (lint/format/typecheck) and `make test-unit`, and diff
   the full unit-test pass/fail count against `main` to confirm no
   regressions elsewhere in the suite.

### Inputs & outputs

**Input:** `feedback: str` (generated review text) and
`context_chunks: list[dict]` (retrieved RAG chunks, each with a `"text"`
key). **Output:** unchanged — `check()` still returns a single
`float` faithfulness score in `[0.0, 1.0]`. The fix changes only how
individual claims are classified as supported/unsupported internally; it
doesn't change the method signatures or the shape of the output.

### Risks & unknowns

- **Overfitting the heuristic to English proper-noun capitalization.**
  Capitalized-key-term matching works well for tech terms ("Python", "SQL")
  but would misfire on feedback that doesn't capitalize technology names
  consistently, or on non-English content. Mitigated by the non-stopword
  fallback, but this is still a heuristic, not a semantic check.
- **Loosening the overlap bar could raise false positives for longer
  claims**, not just fix short ones. Verified this doesn't happen by
  re-running `test_feedback_with_no_support_in_context` (a claim that
  should stay unsupported) after the change — confirmed it still scores
  correctly.
- **`_extract_claims`'s new comma/"and" splitting could over-fragment
  claims** in feedback that uses "and" in a non-listing sense (e.g. "fast
  and reliable" describing one trait, not two facts). Not fully solved by
  this fix — flagged here as a known limitation rather than hidden.
- **Pre-existing, unrelated bugs in the same file**: `test_none_context_chunk_text`
  fails on `main` before this change too (a `None`-context crash in
  `check()`'s `" ".join(...)`), and the whole repo has ~180 pre-existing
  ruff errors and several pre-existing mypy stub-resolution failures
  unrelated to this issue. Confirmed via `git stash`/worktree diffing
  against `main` so as not to conflate this issue's scope with existing
  debt.

### Edge cases

- Claim with exactly one capitalized key term, fully present in context →
  supported (the exact bug this issue reports).
- Claim with a capitalized key term absent from context → still
  unsupported (must not become a rubber stamp).
- Claim with no capitalized words at all → falls back to non-stopword
  overlap rather than defaulting to unsupported.
- Compound claim ("Python, JavaScript, and Docker experience") → split into
  three atomic claims, each scored independently.
- Very long feedback/context (hundreds of words) → must not crash or
  slow down materially; covered by existing `test_very_long_feedback` /
  `test_very_long_context`.
- Empty feedback or empty context chunks → unchanged early-return `0.0`
  path in `check()`, not touched by this fix.
