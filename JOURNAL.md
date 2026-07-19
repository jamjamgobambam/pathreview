# JOURNAL

A running record of progress throughout Module 3. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` mentions that the RAG system uses hybrid retrieval blending
vector similarity and BM25 keyword scores, but it never explains how those scores are
actually combined. There is no description of the default weights, no explanation of how
each score is normalized, and no worked example, so a contributor cannot understand or
tune the ranking behavior from the docs alone. The scoring logic lives in
`rag/retriever/hybrid.py` (`HybridRetriever.retrieve()`), which normalizes each modality
to 0–1 and blends them with a 0.7 vector / 0.3 keyword weighting. A successful fix adds a
"Hybrid Retrieval Scoring" section to `docs/ARCHITECTURE.md` covering the formula, the
default weights, normalization, a numerical example, and relevant edge cases.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
