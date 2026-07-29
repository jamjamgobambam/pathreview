## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/24

**Issue title:** Hybrid retriever over-weights keyword results when query contains technology names

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Issue #24 is about how the app decides which resume/README chunks are "relevant" to a search. Right now it always weighs two signals — meaning-based matching and exact keyword matching — by the same fixed amount, no matter what you search for. The problem is that words like "React" or "Python" show up a lot in both resumes and READMEs, so when someone searches for a tech name, the keyword-matching signal overpowers the meaning-based one and pulls in chunks from the wrong document. A good fix would make the app rely less on keyword matching when the search includes a common tech name, so it picks results based on actual relevance instead of just word overlap. This lives in the retrieval code (rag/retriever/hybrid.py), the part of the app that decides what information gets pulled in before an answer is generated.

**Branch name:** fix/24-hybrid-retriever-keyword-weighting

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger