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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** _(filled in follow-up commit — see the commit that adds this Week 8 section)_

**Reproduction summary:**
Because this is a documentation gap (not a runtime bug), I reproduced it by confirming
the formula is absent from the docs while it exists in code: `grep -in
"weight|normali|bm25|blend|formula|min_score" docs/ARCHITECTURE.md` returns only the
single one-line mention at line 60 (no weights, no normalization, no example), whereas the
actual blending lives in `rag/retriever/hybrid.py:58-81`. I then reproduced the scoring
math by re-implementing lines 58–81 in a standalone script over a sample candidate set and
observed the exact blended scores I plan to document (A=1.000, C=0.500, B=0.467; D=0.075
dropped by the default `min_score=0.3`), confirming I understand precisely what is missing
and where it belongs.

**PLAN.md link:** _(filled in follow-up commit)_

**Walkthrough video (recommended):**

**Blockers or open questions:**
- Two adjacent code observations may be out of scope for a docs-only fix but are worth
  flagging in the PR: (a) `retrieve()` fetches `all_chunks` at hybrid.py:50 but never calls
  `keyword_searcher.index(...)`, so the keyword arm can be empty; (b) the similarity comment
  at vector_store.py:102 says "euclidean" while the collection is created with cosine space
  (vector_store.py:36). I plan to document intended behavior and note these separately rather
  than fix code in this issue.
