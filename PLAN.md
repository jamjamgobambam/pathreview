## Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula — https://github.com/ascherj/pathreview/issues/36

### Understand

`docs/ARCHITECTURE.md` introduces hybrid retrieval conceptually (line 60: "Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context...") but never explains **how the two scores are combined**, what the **default weights** are, or how results are normalized, filtered, and ranked. The actual scoring logic lives in `rag/retriever/hybrid.py`, so today a reader has to open the source to understand it.

- **Expected:** A reader of the architecture doc can understand the hybrid scoring formula, the default weights, the 0–1 normalization, the score threshold, and a concrete worked example — without reading the code.
- **Actual:** The doc only says "vector similarity + BM25 keyword." The formula, weights (`0.7` / `0.3`), normalization, and `min_score` filtering are all undocumented.

This is a documentation gap, not a runtime bug — the fix is doc-only.

### Map

Files I expect to touch:
- **`docs/ARCHITECTURE.md`** — the file being fixed. Add a "Hybrid Retrieval Scoring" subsection near the existing RAG/retrieval description (around line 60).

Files I'll read as the source of truth (reference only, not edited):
- **`rag/retriever/hybrid.py`** — defines the scoring in `HybridRetriever.retrieve()`:
  - default weights `vector_weight=0.7`, `keyword_weight=0.3` (line 14)
  - per-set 0–1 normalization by dividing by the max score (lines 58–59, 70, 76)
  - blended score `vector_weight * vector_score + keyword_weight * keyword_score` (lines 78–81)
  - `min_score=0.3` filter, descending sort, top `max_chunks` (lines 92–97)
- **`rag/retriever/keyword_search.py`** — where BM25 scores (`bm25_score`) come from.
- **`rag/retriever/vector_store.py`** — where vector similarity scores come from.

### Plan

1. Read `hybrid.py`, `keyword_search.py`, and `vector_store.py` closely to confirm the exact formula, defaults, normalization, and threshold behavior currently in the code.
2. Add a new "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md` stating the formula: `blended = vector_weight * norm(vector_score) + keyword_weight * norm(keyword_score)`.
3. Document the default weights (`0.7` vector / `0.3` keyword), the 0–1 normalization step, and the `min_score` (0.3) filter + top-`max_chunks` ranking.
4. Add a short worked numeric example showing how one chunk's vector and keyword scores blend into a final score.
5. Cross-link the doc section back to `rag/retriever/hybrid.py` so the doc and code stay discoverable together.

### Inputs & outputs

- **Input:** the current `docs/ARCHITECTURE.md` and the scoring behavior defined in `rag/retriever/hybrid.py`.
- **Output:** a new documentation subsection in `docs/ARCHITECTURE.md` explaining the formula, default weights, normalization, threshold, and a worked example. No code behavior changes.

### Risks & unknowns

- **Doc/code drift:** if the default weights or `min_score` change later in `hybrid.py`, the doc goes stale. Mitigate by citing the file/line and framing values as "current defaults."
- **How much BM25 to explain:** unsure whether to explain the BM25 algorithm itself or treat it as a black-box score source from `keyword_search.py`. Leaning toward the latter to keep scope tight to issue #36.
- **Example accuracy:** the worked example numbers must reflect the real normalization (dividing by the per-set max in `hybrid.py:58–59`), or the doc would mislead readers.

### Edge cases

The documentation should describe the behaviors the code already handles:
- A chunk found by only **one** searcher (vector OR keyword) — the missing side scores `0` and the chunk still contributes via the weighted sum (`hybrid.py:66–76`).
- The `min_score` threshold filtering out **all** results (empty return).
- Empty result sets or zero max scores, where normalization guards against divide-by-zero (`hybrid.py:70, 76`).
