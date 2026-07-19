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