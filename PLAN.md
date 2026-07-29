## Solution plan

**Issue:** [[Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)]

### Understand
Root cause: `docs/ARCHITECTURE.md:60` describes hybrid retrieval only qualitatively ("vector similarity + BM25 keyword"). It never states the blending formula, the default weights, the per-side normalization step, or the score-floor cutoff that are actually implemented in `rag/retriever/hybrid.py`.

Expected: a reader of the architecture doc can explain how a chunk's final rank is produced and knows which knobs (weights, threshold) exist to retune it, without opening the retriever source.

Actual: the doc gives no formula, no weight values, and no mention of normalization or filtering, so that reasoning is only possible by reading `hybrid.py` directly.

### Map
- `docs/ARCHITECTURE.md` — the file to edit; add a subsection near line 60 under the RAG system description.
- `rag/retriever/hybrid.py` — `HybridRetriever.retrieve()` (lines 28–104): source of truth for the blending formula, default weights (`vector_weight=0.7`, `keyword_weight=0.3`), per-side max-score normalization, and the `min_score=0.3` cutoff applied to the *blended* score.
- `rag/retriever/vector_store.py` — `VectorStore.query()` (line ~103): produces the raw vector score via `similarity = 1 / (1 + distance)`. Collection is created with `hnsw:space: cosine` (line 36), but this conversion formula is the Euclidean form, not the cosine form (`1 - distance`) — need to decide how to handle this before documenting it as fact.
- `rag/retriever/keyword_search.py` — `KeywordSearcher.search()` (line 30): produces the raw `bm25_score` via `BM25Okapi`.

No runtime code changes are expected to be in scope for this issue (it's a docs issue) unless we decide to bundle the cosine/Euclidean fix — see Risks below.

### Plan
1. Confirm the end-to-end formula by re-reading `hybrid.py`, `vector_store.py`, and `keyword_search.py` (done — see Understand/Map).
2. Decide how to handle the cosine-vs-Euclidean discrepancy in `vector_store.py` before writing docs: (a) document current behavior as-is with a caveat, (b) fix the formula in this PR and document the corrected version, or (c) document as-is and file a separate follow-up issue. Needs a decision — see Risks.
3. Draft a new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md`: state the formula (`score = vector_weight * norm(vector_score) + keyword_weight * norm(keyword_score)`), the default weights, and the max-score normalization step in words.
4. Add one worked numeric example: a raw vector distance → similarity → normalized value, a raw BM25 score → normalized value, blend them, and compare the result against the 0.3 cutoff to show why a chunk is kept or dropped.
5. Proofread the new section against the actual source line-by-line for accuracy, then open the PR for review.

### Inputs & outputs
Input: current `docs/ARCHITECTURE.md` content plus the retrieval source in `rag/retriever/`.
Output: an updated `docs/ARCHITECTURE.md` with a formula section, default weight values, and one worked example. No behavioral/runtime changes unless the cosine-formula fix is bundled in (pending the decision in step 2).

### Risks & unknowns
- Whether to fix the cosine/Euclidean similarity bug in `vector_store.py` as part of this PR, or just document current behavior and file it separately — affects whether this PR touches code at all.
- The default weights (0.7/0.3) don't appear to be justified/tuned anywhere in the repo (no comments, tests, or benchmarks referencing why); the doc should present them as defaults, not as an empirically validated choice.
- `min_score=0.3` filters the *blended* score, not either individual sub-score — easy to misstate in prose, need to be precise.

### Edge cases
- A chunk retrieved by only one of the two methods (vector-only or keyword-only) gets an implicit `0.0` for the other side's score but can still clear the blended threshold.
- Empty result sets: `vector_scores_max`/`keyword_scores_max` default to `1.0` via `max(..., default=1.0)` to avoid divide-by-zero — worth a one-line mention so the doc isn't silently wrong for empty collections.
- All candidates scoring below 0.3 after blending → retriever returns an empty list to the generator; doc should note this is a valid, expected outcome.