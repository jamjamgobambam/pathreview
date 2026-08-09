## Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula — https://github.com/ascherj/pathreview/issues/36

### Understand
`docs/ARCHITECTURE.md` describes hybrid retrieval only at a high level ("vector similarity + BM25 keyword" search) but never explains how the two scores are combined. Expected: a developer reading the doc should be able to reproduce the blended score by hand — formula, normalization, and default weights all documented. Actual: the doc stops at naming the two search methods, so the scoring logic and default configuration (`vector_weight=0.7`, `keyword_weight=0.3`) are only discoverable by reading `rag/retriever/hybrid.py` directly. This is a docs-only gap — the underlying code already implements the blend correctly.

### Map
- `docs/ARCHITECTURE.md` — RAG System subsystem section (around line 59-60) — the file to edit.
- `rag/retriever/hybrid.py` — `HybridRetriever` class, source of truth for the formula: weights ([hybrid.py:13-14](rag/retriever/hybrid.py#L13-L14)), score normalization ([hybrid.py:58-59](rag/retriever/hybrid.py#L58-L59)), blending ([hybrid.py:78-81](rag/retriever/hybrid.py#L78-L81)), and `min_score` filtering ([hybrid.py:29](rag/retriever/hybrid.py#L29)).
- `rag/retriever/keyword_search.py` — reference only, not edited; needed to understand where `bm25_score` comes from.

### Plan
1. Re-verify formula, normalization, and default weights against current `rag/retriever/hybrid.py` (already confirmed once during Week 8 reproduction — recheck at PR time in case the code drifted).
2. Add a new "Hybrid Retrieval Scoring" subsection under RAG System in `docs/ARCHITECTURE.md` stating the blend formula, the normalization step, and the default weights.
3. Add a worked example (3 candidate chunks: one matched by both searches, one vector-only, one keyword-only) showing the normalized scores and final blended score, adapted from the draft in JOURNAL.md into doc-appropriate, concise prose/table.
4. Note the `min_score` interaction briefly — i.e., that a low-weight keyword-only match can still clear or miss the default threshold — since it explains real ranking behavior, not just the math.
5. Proofread the new section against the live code one more time, then open the PR on the `docs/36-...` branch linking back to issue #36.

### Inputs & outputs
- Input: current `docs/ARCHITECTURE.md` content, plus the verified behavior of `HybridRetriever.retrieve` (formula, weights, normalization, filtering).
- Output: an updated `docs/ARCHITECTURE.md` with a dedicated scoring subsection (formula, default weights, worked example) under RAG System. No production code changes.

### Risks & unknowns
- Default weights or line references could drift if `hybrid.py` changes before this merges — re-verify against the current file right before opening the PR, not just from journal notes.
- Open question: whether to mention the `keyword_searcher.index()` runtime bug found during reproduction (chunks fetched by `_get_all_chunks` are never passed to `index()` before `.search()`, so keyword scores can be empty at runtime). It's out of scope for this docs-only issue, but documenting a formula that isn't actually exercised at runtime could be misleading. Leaning toward a one-line "known limitation" note plus a separate follow-up issue, rather than silently ignoring it — need to confirm with reviewer/maintainer.
- Keep the addition concise and consistent with the terse style of the rest of `ARCHITECTURE.md` — the JOURNAL.md draft is more verbose than the doc's existing tone and will need trimming.

### Edge cases
- Chunk returned by only one of the two searches — the missing side's score is 0, not excluded from blending; the worked example should show this explicitly.
- Degenerate case where the max score in a result set is 0 — code already guards this (`if vector_scores_max > 0 else 0`), worth a one-line mention so readers know it's handled rather than undefined.
- A keyword-only match with a strong BM25 score can still fall below `min_score` because of the low default `keyword_weight` — this is the main behavioral nuance the worked example needs to surface.
