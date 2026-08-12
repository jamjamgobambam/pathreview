## Week 7 — Issue selection

**Issue link:** https://github.com/<org>/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** Tier 1

**Problem summary:**
The `_is_supported()` method in `rag/evaluator/faithfulness_checker.py` determines
whether a generated claim is backed by the retrieved context by requiring at least
two overlapping non-stopword tokens between the claim and the context. This
threshold breaks down for short factual claims. A sentence like "The candidate
knows Python" only shares one meaningful token with a supporting context like "python expert," 
so it gets marked unsupported even though it's accurate. As a result, any feedback made up of short, well-supported claims
scores 0.0, which misrepresents genuinely faithful output as unfaithful. The fix will involves adjusting the overlap threshold to scale with claim length.
This affects the `rag` module's evaluation layer, `FaithfulnessChecker`, and existing unit tests already capture the expected behavior once fixed.

**Branch name:** fix/152-faithfulness-checker-short-claims

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger


**Checklist reasoning:**

*Part 1 — Understanding:* The issue is that `_is_supported()` in the faithfulness
checker requires 2+ overlapping non-stopword tokens between a claim and its
context, but short claims often only share 1 actually meaningful token with a fully supporting context, so they always score as unsupported. It should be a short, accurate claim like "Knows Python" backed by context
like "python expert" should score as supported.

*Part 2 — Tier fit:* Tagged Tier 1. This is my first time tackling an issue in a large codebase

*Parts 3 and 4:* I believe it will take me around 3 hours to debug given the failing tests

## Week 8 - Reproduction of Issue

## Week 8 — Reproduction & solution planning

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/landon517/pathreview/commit/a3f670ecac2b9bfebc9413ceb58d987cb55704ab)

**Reproduction summary:**
Ran the failing tests and the repro script from issue #152; confirmed the
faithfulness checker returns 0.0 for claims that should be fully supported,
because `_is_supported()`'s hardcoded overlap threshold of 2 tokens can't be
met by short claims.

**PLAN.md link:** 

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Also noticed `test_none_context_chunk_text` fails with a TypeError — appears
unrelated to #152 (crashes on None context text rather than a scoring issue),
treating as out of scope for this fix.


## Week 9 — Solution building & PR submission
 
### Check-in 1
 
**Current progress:**
Sub-tasks 1–4 from `PLAN.md` are done. I reproduced the bug locally and confirmed
the failing tests all trace back to the same root cause rather than separate
defects. I read `_is_supported()` in full and enumerated its three tunable pieces
— the hardcoded stopword literal, the `.split()` tokenization, and the `>= 2`
threshold constant — and grepped for callers to confirm `_is_supported()` is only
used from `check()` within `faithfulness_checker.py`, so changing its behaviour
doesn't ripple into other evaluators.
 
I settled the design question from sub-task 3 in favour of a scaled absolute
threshold over a ratio: claims with ≤ 2 meaningful tokens must match all of them,
claims with 3+ keep the original `>= 2` rule. A ratio would have changed scoring
for every claim length rather than only the short-claim case in the issue.
 
While reproducing I confirmed the tokenization wrinkle I flagged in `PLAN.md` was
real — plain `.split()` leaves trailing punctuation attached, so `"python."` never
matched the context token `"python"`. Fixed that with a `\b\w+\b` regex in the same
change, since the threshold fix alone wouldn't have resolved the reported example.
 
**Next steps:**
Sub-task 5 — finish the regression tests, run the full test file, and check for
regressions in longer-claim cases. Then `make check`, self-review against
`docs/CONTRIBUTING.md`, and open the draft PR for feedback.
 
**Blockers:**
Two tests in this file fail on `main` for reasons unrelated to #152 and I need to
document them rather than fix them. `test_none_context_chunk_text` is issue #153 —
a `TypeError` in `check()` when a chunk has `text: None` — which is a separate
defect and out of scope here. `test_partial_support_returns_middle_score` looks
unfixable from `_is_supported()` at all; confirming that before I write it up.
 
---
 
### Check-in 2 
 
**PR link:** https://github.com/ascherj/pathreview/pull/970

**Branch:** `fix/152-faithfulness-checker-short-claims`
 
**What you built:**
Replaced the hardcoded 2-token overlap threshold in
`FaithfulnessChecker._is_supported()` with one that scales to claim length —
claims with 2 or fewer meaningful tokens must have all of them appear in the
context, while longer claims keep the original `>= 2` rule. Also switched
tokenization from `str.split()` to a `\b\w+\b` regex so trailing punctuation no
longer blocks a match, and added an explicit guard returning `False` for claims
made up entirely of stopwords. Short, fully-supported claims now score as
supported instead of being forced to 0.0 by their length.
 
**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — five tests added.
`test_short_claim_single_token_overlap_scores_supported` is the regression test
for the exact case in #152. `test_short_claim_no_overlap_stays_unsupported` guards
against the fix over-loosening the checker. `test_zero_meaningful_token_claim`
covers a stopword-only claim. `test_check_end_to_end_with_short_claims` exercises
the full `check()` path with a mix of short and normal claims.
`test_extract_claims_drops_very_short_claims` documents the pre-existing
`len(claim) > 10` filter in `_extract_claims()`, which drops claims like
`"Knows SQL"` before they reach `_is_supported()` — relevant context for anyone
reading the issue later. Three previously-failing tests named in the issue now
pass: `test_short_claim_single_token_overlap_scores_supported`,
`test_multiple_context_chunks`, and `test_multiple_claims_varying_support`.
 
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
 
*Both in the sense the assignment defines for a codebase with documented
pre-existing failures: my changes introduce no new failures. Two tests in
`tests/unit/test_faithfulness_checker.py` failed on `main` before this branch and
still fail after it, both documented in the PR description.
`test_none_context_chunk_text` is issue #153, a separate `TypeError` in `check()`
when a context chunk has `text: None`, deliberately left out of scope to keep this
PR to one issue. `test_partial_support_returns_middle_score` cannot pass under any
change confined to `_is_supported()`: its feedback is a single sentence, so
`check()` sees exactly one claim and can only return 0.0 or 1.0, while the test
asserts a score strictly between 0.2 and 0.8. Making it pass would require graded
per-claim scoring, and even that doesn't resolve it cleanly — its claim is
numerically identical to the one in `test_feedback_with_no_support_in_context`
under token overlap (6 meaningful tokens, 1 overlapping, 7-token context) while the
two tests require different score bands, so separating them needs term weighting or
semantic similarity rather than token counts. That's a redesign of the scoring
layer, outside the scope of #152.*
 
**Draft PR feedback received from:** TODO — Slack handle of whoever reviews it, or "none"
