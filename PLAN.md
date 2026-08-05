# Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula — https://github.com/ascherj/pathreview/issues/36

### Understand
The root cause is a documentation gap, not a code bug: `docs/ARCHITECTURE.md` describes the RAG subsystem as using "hybrid retrieval (vector similarity + BM25 keyword)" but stops there. Expected behavior: a contributor reading the architecture doc should understand how the final ranking score is computed without reading `rag/retriever/hybrid.py`. Actual behavior: the doc gives no formula, no default weights, and no explanation of normalization or filtering, so the only way to learn this is to read the implementation directly.

### Map
- `docs/ARCHITECTURE.md` — the file to edit; add a new subsection under "RAG System" (around line 59-60) explaining the scoring formula.
- `rag/retriever/hybrid.py` — source of truth for the actual logic (`HybridRetriever.retrieve`, lines 28-104): min-max normalization (lines 57-59), weighted blend (lines 78-81), min-score filter (line 93), sort/truncate (lines 94-97), and default weights in `__init__` (line 14: `vector_weight=0.7, keyword_weight=0.3`).
- `rag/retriever/vector_store.py` and `rag/retriever/keyword_search.py` — not modified, but skimmed to accurately describe what `score` and `bm25_score` represent in the doc.

### Plan
1. Re-read `HybridRetriever.retrieve` end-to-end and write out the formula in plain language and as a short equation (normalized_vector * vector_weight + normalized_keyword * keyword_weight).
2. Draft a new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md` covering: the two input scores, the normalization step, the default weight values, the min_score filter, and how chunks found by only one method are scored (missing side treated as 0).
3. Add a concrete worked example (e.g., a chunk with vector_score=0.8, normalized against a max, blended with a keyword score) so the math is verifiable by a reader.
4. Cross-check the written explanation against the code line-by-line to make sure no detail (e.g., normalization uses the max of the *current result set*, not a global max) is misstated.
5. Proofread, verify markdown renders correctly, and commit with a `docs(rag):` scoped conventional commit message per `CONTRIBUTING.md`.

### Inputs & outputs
**Input:** the existing `docs/ARCHITECTURE.md` file and the current `rag/retriever/hybrid.py` implementation (read-only reference).
**Output:** an updated `docs/ARCHITECTURE.md` with a new subsection documenting the hybrid scoring formula, default weights, and a worked example. No code changes.

### Risks & unknowns
- Risk: describing the normalization step incorrectly (it's max-only normalization, not min-max in the strict sense — `score / max_score`, no subtraction of a min) — mitigated by quoting the exact lines in `rag/retriever/hybrid.py:57-59` rather than paraphrasing from memory.
- Unknown: whether the default weights (0.7/0.3) are ever overridden elsewhere in the codebase (e.g., dependency injection/config) — need to grep for `HybridRetriever(` call sites before asserting "0.7/0.3 is always the default in practice."
- Risk: the worked example needs realistic numbers; if I invent values that don't reflect real score ranges (e.g., BM25 scores aren't bounded 0-1 before normalization), the example could mislead readers — will double check `keyword_search.py` for the actual score range BM25 produces.

### Edge cases
- A chunk that appears in vector results but not keyword results (and vice versa) — doc should state the missing side is treated as score 0, not excluded.
- Empty result sets from either search (division by max score when max is 0) — code guards this with `if vector_scores_max > 0 else 0`; doc should mention this guard so readers aren't confused about divide-by-zero.
- All results falling below `min_score` — doc should note the retriever can return an empty list in this case.
