# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` states that the RAG system uses "hybrid retrieval (vector similarity + BM25 keyword)" but never explains how the two scores are actually combined into a final ranking. The real logic lives in `rag/retriever/hybrid.py`: vector and BM25 scores are each min-max normalized against the max score in their result set, then blended with configurable weights (defaulting to 0.7 vector / 0.3 keyword), filtered against a minimum score threshold, and sorted to produce the final ranked chunks. Because none of this is documented, a new contributor reading the architecture doc has no way to know the default weights, the normalization step, or how ties/missing results (a chunk found by only one method) are handled. A successful fix adds a section to `docs/ARCHITECTURE.md` that explains the formula, states the default weights, and walks through a concrete worked example so future contributors can reason about retrieval behavior without reading the implementation.

**Branch name:** issue-36-docs

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [add link after pushing the reproduction commit]

**Reproduction summary:**
This is a documentation gap, not a runtime bug, so "reproducing" it means confirming exactly what's missing and where. I read `docs/ARCHITECTURE.md:59-60`, which only says hybrid retrieval "fetches relevant context" via vector + BM25 without describing the scoring math, then traced the real behavior in `rag/retriever/hybrid.py:57-94`: both score types are min-max normalized independently, blended with `vector_weight=0.7` / `keyword_weight=0.3` defaults, filtered by `min_score`, and sorted descending. I confirmed the doc has no mention of the weights, the normalization step, or the min-score filter — matching the issue's description exactly.

**PLAN.md link:** [PLAN.md](PLAN.md)



**Blockers or open questions:**
None yet — the fix is scoped to a single doc file, so risk is low going into Week 9.
