# Solution plan

**Issue:** [#36 — Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)

### Understand
`docs/ARCHITECTURE.md` says the RAG system uses "hybrid retrieval (vector similarity + BM25 keyword)" but never explains how the two scores are combined. Expected behavior: a reader should be able to understand, from the docs alone, exactly how a chunk's final ranking score is derived. Actual behavior: the doc gives no formula, no default weights, and no example — you have to read `rag/retriever/hybrid.py` to find out.

Root cause (read in `rag/retriever/hybrid.py:44-94`): `HybridRetriever.retrieve()`
1. Runs vector search (`VectorStore.query`) and BM25 keyword search (`KeywordSearcher.search`) independently, each returning up to `max_chunks * 2` candidates.
2. Min-max normalizes each side **within its own result set**: `vector_score / max(vector_scores)` and `bm25_score / max(bm25_scores)` (lines 58-59, 70, 76). Note this is normalization against the max of the *retrieved* candidates, not a global max — so the same raw score can normalize differently across queries.
3. Blends the two normalized scores with a weighted sum: `score = vector_weight * vector_norm + keyword_weight * keyword_norm`, with defaults `vector_weight=0.7`, `keyword_weight=0.3` (`hybrid.py:14`).
4. Filters out anything below `min_score` (default 0.3) and returns the top `max_chunks` by blended score.

Worked example to include in the doc (hand-verified, not from a test since none exist yet):
- Chunk A: raw vector score 0.82, raw BM25 score 4.1
- Chunk B: raw vector score 0.75, raw BM25 score 6.5
- Normalize against max(0.82, 0.75)=0.82 and max(4.1, 6.5)=6.5:
  - A: vector_norm = 0.82/0.82 = 1.00, keyword_norm = 4.1/6.5 = 0.63 → score = 0.7(1.00) + 0.3(0.63) = 0.889
  - B: vector_norm = 0.75/0.82 = 0.91, keyword_norm = 6.5/6.5 = 1.00 → score = 0.7(0.91) + 0.3(1.00) = 0.940
  - Result: B outranks A despite a lower vector score, because its stronger keyword match is enough to overcome the 0.7/0.3 weighting.

### Map
Files to touch (docs only — no retrieval-path code changes, per issue scope):
- `docs/ARCHITECTURE.md` — add a subsection under "RAG System" with the formula, default weights, and the worked example above; remove the reproduction comment added this week.
- No changes to `rag/retriever/hybrid.py` or `rag/retriever/keyword_search.py` — read-only, to source the formula accurately.

### Plan
1. Read `rag/retriever/hybrid.py` and `rag/retriever/keyword_search.py` once more to double check nothing changes between now and implementation (defaults, normalization order).
2. Draft a new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md`: state the two inputs (vector similarity, BM25), the min-max normalization step, the weighted-sum formula, and the default weights with a one-line rationale (favor semantic match, keyword as tiebreaker/boost).
3. Add the worked example as a small table or short walkthrough so the arithmetic is checkable.
4. Replace the reproduction `<!-- ISSUE #36 ... -->` comment with the finished section.
5. Proofread against the actual code once more (defaults, variable names) before opening the PR, since this doc is the only source of truth once merged.

### Inputs & outputs
- Input: the existing `docs/ARCHITECTURE.md` file and the current implementation in `rag/retriever/hybrid.py`.
- Output: an updated `docs/ARCHITECTURE.md` with an explicit formula, stated defaults (`vector_weight=0.7`, `keyword_weight=0.3`), and a worked numeric example. No other files change.

### Risks & unknowns
- `rag/retriever/hybrid.py` fetches all chunks via `_get_all_chunks` (line 50) but never appears to call `keyword_searcher.index(all_chunks)` before calling `.search()` in `retrieve()` — the BM25 index seems to depend on being built elsewhere (ingestion?). This looks like a separate bug, out of scope for issue #36, but I should confirm where/whether indexing actually happens before I describe the keyword-search step in the doc, so I don't document a code path that's currently unreachable in practice.
- Per-query min-max normalization (not global) means the doc needs to be careful to say scores are relative to the current candidate set, not an absolute 0-1 quality measure — easy to accidentally overstate in the writeup.
- No existing tests cover `HybridRetriever`, so the worked example is verified by hand rather than by running the actual code — low risk since the arithmetic is simple, but worth double-checking line numbers/defaults haven't drifted before the final PR.

### Edge cases
- Empty vector or keyword result set (division-by-default handled via `max(..., default=1.0)` in code) — worth a one-line mention in the doc so readers aren't surprised by a chunk with a 0 component score.
- A chunk found by only one of the two search methods (its missing side contributes 0, not filled in with the other's value) — should be called out explicitly since it affects how "hybrid" the ranking really is for keyword-only or vector-only matches.
