## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview generates portfolio feedback with a RAG pipeline, and a faithfulness checker scores whether each claim in that feedback is actually backed by the retrieved source text. The check lives in rag/evaluator/faithfulness_checker.py, in the _is_supported() method. Right now that method only counts a claim as supported when at least two meaningful (non-stopword) words overlap between the claim and the context. Short factual claims like "Knows Python" share only one meaningful word with a fully supporting context, so they are always scored as unsupported, and feedback made of short correct claims comes back with a faithfulness score of 0.0. A successful fix lowers that threshold so short, genuinely supported claims are no longer penalized, while claims with no real support still score as unsupported, verified against the three failing tests in tests/unit/test_faithfulness_checker.py.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" reasoning:**
The scope is contained to one method in one file, with a clear definition of done since three existing tests pin down the expected behavior, so I am not guessing at acceptance criteria. It fits my background in LLM output evaluation from my TrendMate chatbot project, where I built the LLM integration and needed the model's output to stay grounded, so I understand why a faithfulness check exists and what a correct fix should preserve. While confirming the bug I also noticed a separate failure (test_none_context_chunk_text) caused by a None context chunk, but that belongs to issue #153, so I am keeping this contribution scoped to the threshold bug in #152.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/lisatran183/pathreview/commit/8fb7f214559be009bc76d886be262b5ddfc4e2d4

**Reproduction summary:**
Ran `pytest tests/unit/test_faithfulness_checker.py -v` locally on the
fix/152-faithfulness-short-claims branch. Confirmed all 3 target tests fail
as the issue describes:
- test_partial_support_returns_middle_score — assert 0.2 < 0.0
- test_multiple_context_chunks — assert 0.0 > 0.5
- test_multiple_claims_varying_support — assert 0.2 < 0.0
(A 4th test, test_none_context_chunk_text, also fails but with a TypeError —
that's the separate None-context bug already scoped to #153, not this issue.)

**PLAN.md link:** https://github.com/lisatran183/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Blockers or open questions:**
Still deciding whether the fix should scale the overlap threshold by claim length (risk: reintroduces false positives from generic shared words like "developer") or move to a continuous per-claim support score instead of a boolean, since some failing tests expect partial (0.2-0.8) scores rather than strict pass/fail.