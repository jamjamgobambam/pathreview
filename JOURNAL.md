# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker` in `rag/evaluator/faithfulness_checker.py` scores generated
feedback by splitting it into claims (sentences) and checking each claim for keyword
overlap with the retrieved context. The `_is_supported()` helper requires at least 2
non-stopword tokens to overlap between a claim and the context text before it counts
the claim as supported. Short factual claims like "Knows Python." contain only one
meaningful token ("python"), so even when the context fully backs the claim (e.g. a
chunk containing "python expert"), the overlap can never reach the threshold of 2 and
the claim is always marked unsupported. This silently zeroes out the faithfulness
score for any feedback made up of short, accurate sentences, which is exactly the
style of feedback this evaluator is meant to check, and it's also why several existing
unit tests (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) currently fail. A successful fix adjusts the
overlap threshold logic so it scales with claim length instead of using a fixed
minimum of 2, so short but genuinely supported claims score correctly.

**Scope reasoning ("Is this right for me?" checklist):**
- Reproduction is already given in the issue (a 3-line script) and reproduces against a
  single function, so I can confirm the bug before writing any code.
- The fix is isolated to one file (`rag/evaluator/faithfulness_checker.py`) and doesn't
  require touching the API, frontend, or any external service — low blast radius.
- There are already three named failing unit tests
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`) that define what "done" looks like, so I have
  a concrete, checkable success criterion rather than an open-ended judgment call.
- Tier-1 label matches this being my first issue in the codebase.
- Risk: I need to make sure the new overlap threshold doesn't just special-case short
  claims but stays consistent for longer ones too — worth checking the full test file,
  not just the three named tests, before opening a PR.

**Branch name:** fix/152-faithfulness-checker-short-claims

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
