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