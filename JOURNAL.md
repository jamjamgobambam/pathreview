## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/24

**Issue title:** Hybrid retriever over-weights keyword results when query contains technology names

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that the keywords are being matched incorrectly and the model will return irrelevant chunks from the wrong document because of similar wordings. What is currently broken is the RAG retrieval system in `rag/retriever/hybrid.py` and a successful fix would be that the correct chunks are being returned for the model to use.

**Branch name:** fix/24-hybrid-retriver

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger