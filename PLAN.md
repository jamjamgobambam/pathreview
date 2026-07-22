## Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula (#36) — https://github.com/ascherj/pathreview/issues/36

### Understand
`docs/ARCHITECTURE.md`'s RAG System section states that hybrid retrieval "blends vector and BM25 keyword scores" but stops there — it never explains how the two scores are combined, what the default weights are, or how results get filtered. Expected behavior: a reader of the architecture doc should be able to predict a chunk's final relevance score without reading source code. Actual behavior: the formula only exists in `rag/retriever/hybrid.py` (`HybridRetriever.retrieve`), where vector and BM25 scores are each normalized to 0–1 (divided by the max score in their respective result set), then blended as `vector_weight * vector_score + keyword_weight * keyword_score` with defaults `vector_weight=0.7`, `keyword_weight=0.3`, and results below `min_score=0.3` are dropped. The root cause is a documentation gap, not a code bug — the fix is entirely in the doc.

### Map
- `docs/ARCHITECTURE.md` — add a new subsection under "RAG System (`rag/`)" explaining the formula, default weights, and threshold. This is the only file that needs to change.
- `rag/retriever/hybrid.py` (`HybridRetriever.__init__`, `HybridRetriever.retrieve`) — source of truth for the formula and defaults; read-only reference, not modified.
- `rag/retriever/keyword_search.py` (`KeywordSearcher.search`) — source of truth for how BM25 scores are produced before blending; read-only reference.
- `docs/adr/` — check whether an existing ADR already covers retrieval design decisions, to link from rather than duplicate.

### Plan
1. Re-read `hybrid.py` and `keyword_search.py` end to end to confirm there's no additional normalization or override path I'm missing (e.g. config-driven weights).
2. Search the codebase for any place `HybridRetriever(...)` is actually constructed, to confirm whether the 0.7/0.3 defaults are the values actually used in production, or whether something overrides them at call time.
3. Draft a new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md`: describe the two signals, the normalization step, the blending formula, and the `min_score` cutoff in plain language plus a short formula line.
4. Add one worked numeric example (e.g., a chunk with vector_score=0.8, keyword_score=0.4 → blended score 0.68) so the abstract formula is concrete.
5. Note in the doc that the weights are constructor parameters (not hardcoded constants), so readers know they're tunable.

### Inputs & outputs
Input: the existing, unchanged logic in `rag/retriever/hybrid.py` and `rag/retriever/keyword_search.py`. Output: an updated `docs/ARCHITECTURE.md` with a new subsection covering the scoring formula, default weights, and a worked example — no application code changes.

### Risks & unknowns
- I couldn't find any call site that actually constructs `HybridRetriever(...)` outside its own file — no tests, no service wiring found yet. Before documenting 0.7/0.3 as "the" defaults, I need to confirm nothing overrides them elsewhere (step 2 above); if I can't find a call site at all, I'll document them as "constructor defaults" rather than implying they're confirmed production values.
- There are no existing unit tests for `HybridRetriever`, so I can't cross-check the formula against test fixtures — I'm relying solely on reading the source.
- Score normalization is per-query (divides by the max score within that query's result set), not a fixed global scale — I need to word this precisely in the doc so it isn't misread as an absolute 0-1 confidence score.

### Edge cases
- Empty result sets: `vector_scores_max`/`keyword_scores_max` default to `1.0` when no results exist, avoiding a divide-by-zero — worth a one-line mention so readers don't assume a bug if they see an empty set behave differently.
- A chunk found by only one retrieval method (vector or keyword, not both) — the doc should show that the missing side's score defaults to 0 rather than being excluded outright.
- `min_score` filtering out every candidate (e.g., a very short or unusual query) — worth noting that this can legitimately return zero chunks, since that's a real possible outcome of the threshold, not a bug.
