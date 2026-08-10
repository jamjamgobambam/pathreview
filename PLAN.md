## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula #36](https://github.com/ascherj/pathreview/issues/36)

### Understand
* **Root Cause:** The system uses a customized relative min-max normalization and independent weights (`vector_weight = 0.7`, `keyword_weight = 0.3`) inside `rag/retriever/hybrid.py`, but this mathematical scoring logic was completely omitted from the architecture overview.
* **Expected vs. Actual:** Developers checking `docs/ARCHITECTURE.md` expect to see the blending equations and default constraints. Actually, the document only mentioned that blending happens without detailing *how*.

### Map
* `rag/retriever/hybrid.py` (To inspect parameters, normalization rules, and blending lines 78-81)
* `docs/ARCHITECTURE.md` (The document requiring the update)

### Plan
1. Locate and extract the exact formula matching logic from `rag/retriever/hybrid.py`.
2. Draft clean LaTeX formatting blocks for the normalization and linear combination equations.
3. Inject the configuration constraints (weights `0.7`/`0.3`, `min_score` cutoff `0.3`, max chunks limit `10`) into the file.
4. Construct a clear numeric edge-case example showing a item found by only one search modality.

### Inputs & outputs
* **Input:** Raw search components and engine defaults from `hybrid.py`.
* **Output:** A structural breakdown containing clear Markdown math notation added to the main architecture document.

### Risks & unknowns
* **Risks:** Using incorrect LaTeX styling constraints that break rendering on GitHub. (Mitigated by testing layout standard formatting).

### Edge cases
* **Modal Misses:** A chunk found exclusively by one algorithm. The documentation must clearly explain that a missing modality receives a score of `0.0` rather than crashing the calculation.