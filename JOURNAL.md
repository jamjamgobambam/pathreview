## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The documentation for `ARCHITECTURE.md` does not have additional detail apart from architecture: Hybrid retrieval (vector similarity + BM25 keyword). A successful fix should elaborate on the scoring formula used, and the heuristic behind the scoring formula. It affects  `docs/ARCHITECTURE.md` only, to explain the folder  `rag`, which includes `hybrid.py`, `keyword_search.py`, and `vector_store.py`.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

PR message:

docs(rag): include hybrid retrieval scoring formula for the RAG system.

docs/ARCHITECTURE.md does not have additional detail apart from architecture: Hybrid retrieval (vector similarity + BM25 keyword). Does not elaborate how the vector similarity is calculated, and what BM25 keyword is used. Added mathematical formulas + explanation for the current model.

Added formulas and explanation of hybrid retrieval system for RAG.

Docs #36