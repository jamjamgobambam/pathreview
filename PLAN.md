## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula #36](https://github.com/ascherj/pathreview/issues/36)

### Understand

The root cause is a documentation gap, not a code bug. `docs/ARCHITECTURE.md` mentions that PathReview uses hybrid retrieval — blending vector similarity and BM25 keyword search — but never explains how the two scores are combined. The implementation in `rag/hybrid.py` performs per-method min-max normalization (dividing each raw score by the highest score that method returned) and then computes a weighted sum with a default vector weight of `0.7` and a keyword weight of `0.3`. It also filters out any chunk whose final hybrid score falls below a minimum threshold before sorting and returning the top-k results.

**Expected behavior:** A contributor reading `docs/ARCHITECTURE.md` can understand the full ranking pipeline — normalization, formula, default weights, threshold filtering, and how to interpret the output — without needing to read source code.

**Actual behavior:** The doc stops at "vector and keyword scores are blended" with no formula, no weights, no example, and no description of filtering or sorting.

### Map

Only one file needs to be changed:

- `docs/ARCHITECTURE.md` — add a new subsection under the RAG System section explaining hybrid retrieval scoring

Files to read for accuracy (no changes needed):

- `rag/hybrid.py` — source of truth for the normalization logic, weight constants, threshold, and sort order

### Plan

1. Re-read `rag/hybrid.py` in full and confirm the exact variable names, default values, and any configurable parameters (e.g., whether weights or threshold are overridable by callers).
2. Draft the new subsection in `docs/ARCHITECTURE.md` covering: (a) per-method score normalization, (b) the weighted-sum formula, (c) the default weights and what they mean, (d) the minimum-score filter, and (e) final sort and top-k selection.
3. Add a concrete numerical example showing two chunks going through every step — raw scores → normalized scores → weighted sum → filter → ranked output.
4. Verify the written formula and example against `rag/hybrid.py` line by line so nothing is invented or paraphrased incorrectly.
5. Commit the updated `docs/ARCHITECTURE.md` on branch `docs/36-hybrid-retrieval-scoring` and confirm the doc renders correctly on GitHub.

### Inputs & outputs

**Input:** The existing `docs/ARCHITECTURE.md` file and the implementation in `rag/hybrid.py`.

**Output:** A new subsection in `docs/ARCHITECTURE.md` — likely titled "Hybrid Retrieval Scoring" — containing the normalization description, the formula `hybrid_score = 0.7 × vector_norm + 0.3 × bm25_norm`, the default weights, the filtering rule, and a worked numerical example. No source code changes.

### Risks & unknowns

- **Risk — documenting assumptions:** The formula and weights in this plan came from reading `rag/hybrid.py` during Week 7. Before finalizing the doc, I need to re-read the file to confirm nothing changed and that I haven't misread any variable (e.g., whether weights are module-level constants or function defaults).
- **Risk — missing configurability:** If `rag/hybrid.py` accepts `vector_weight` or `threshold` as parameters, the doc should note what the defaults are and that callers can override them. This needs to be verified before writing.
- **Risk — doc placement:** `docs/ARCHITECTURE.md` may already have a RAG section with specific formatting conventions. The new subsection needs to match the heading depth and style of the surrounding content.
- **Unknown:** Whether there is a minimum-threshold value hardcoded or imported from a config file — this affects how precisely the doc can describe the filter step.

### Edge cases

- **All chunks score below threshold:** The filter should return an empty list rather than a runtime error; the doc should note this is possible if a query has no relevant matches.
- **Single retrieval method returns no results:** If BM25 returns nothing, the BM25 term in the formula is effectively zero for all chunks; the doc should clarify that the formula still applies and that normalization is skipped for the empty result set.
- **Tied hybrid scores:** When two chunks have the same final score, their relative order is determined by whatever sort stability Python provides — this is worth a brief note so contributors don't expect deterministic tiebreaking.
- **Non-default weights:** A caller passing `vector_weight=0.5` shifts to equal weighting; the doc should make clear that `0.7 / 0.3` are defaults, not fixed values, so the formula reads as general before the defaults are introduced.
