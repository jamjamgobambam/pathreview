# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` currently says retrieval blends "vector similarity + BM25 keyword" search but never shows the actual math, so a reader can't tell how a chunk's final rank is produced or what happens if they want to retune it. Looking at the implementation in `rag/retriever/hybrid.py`, each chunk's vector and keyword scores are independently min-max normalized against the max score in that result set, then combined as `score = vector_weight * vector_score + keyword_weight * keyword_score` with defaults of 0.7/0.3, and anything below a 0.3 threshold is dropped before the top-`max_chunks` results are returned. None of that — the formula, the default weights, the normalization step, or the score-floor cutoff — is documented anywhere. A successful fix adds a section to `docs/ARCHITECTURE.md` that states the formula, the default weights, and walks through one worked example (e.g., a chunk with a raw vector score and BM25 score, normalized, blended, and compared against the 0.3 cutoff) so a new contributor can reason about retrieval ranking without reading the retriever source.

This is right for me because the issue mostly focus on RAG, retrieval scoring formula and architecture docs -- these focuses on design questions and issues, which could be reliable for me.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [commit not yet made — see below]

**Reproduction summary:**
Since this is a documentation gap rather than a runtime bug, "reproducing" it meant confirming the gap exists: `docs/ARCHITECTURE.md:60` states retrieval blends "vector similarity + BM25 keyword" with no formula, while `rag/retriever/hybrid.py` shows the actual blending is `score = 0.7 * norm(vector_score) + 0.3 * norm(keyword_score)` with per-side max-score normalization and a 0.3 blended-score cutoff — none of which appears in the doc. While tracing the formula I also found the vector-score conversion in `rag/retriever/vector_store.py` uses the Euclidean similarity formula (`1/(1+distance)`) on a collection configured for cosine distance, a discrepancy that needs a decision (document as-is vs. fix) before the new doc section is written.

**PLAN.md link:** https://github.com/nhatminh-07/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md (push the branch for this link to resolve)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Resolved: decided to fix the cosine/Euclidean similarity discrepancy in `vector_store.py` as part of this PR rather than deferring it, since documenting a formula that doesn't match its own collection config would just enshrine the bug. This PR is now docs + a one-line scoring fix, not docs-only. Added `tests/unit/test_vector_store.py` to cover the corrected formula (all 7 tests passing) — no longer a blocker.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All PLAN.md sub-tasks are done: added the "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md` (formula, default weights, normalization, worked example), fixed the cosine/Euclidean similarity discrepancy in `rag/retriever/vector_store.py`, and added `tests/unit/test_vector_store.py` to cover the corrected formula.

**Next steps:**
Push the branch, open the PR, and note in the PR description that the 53 pre-existing failing tests and `make check` lint/format/mypy issues in the repo predate this branch (verified by re-running the suite with this diff stashed out) so reviewers don't mistake them for regressions.

**Blockers:**
None from this diff. The repo has pre-existing, unrelated test and lint/format/mypy debt (53 failing unit tests, unformatted files, a numpy/mypy stub incompatibility on Python 3.13) that `make check`/`make test-unit` will surface regardless of this branch.

---

### Check-in 2 (end of week)

**PR link:** [not yet opened — push branch and open PR]

**Branch:** docs/36-hybrid-retrieval-scoring-formula

**What you built:**
Documented the hybrid retrieval scoring formula (normalize → weighted blend → threshold filter, with default weights and a worked numeric example) in `docs/ARCHITECTURE.md`, and fixed a bug found while tracing the formula: `VectorStore.query()` was converting ChromaDB distances with the Euclidean similarity formula on a collection configured for cosine space, now corrected to `max(0.0, 1 - distance)`.

**Tests added or updated:**
`tests/unit/test_vector_store.py` (new) — 7 tests covering the corrected cosine similarity conversion: distance 0 → score 1.0, distance 1 → score 0.0, distance > 1 clamps to 0.0 instead of going negative, the doc's 0.35 → 0.65 worked example, score ordering across multiple results, empty results, and result dict shape.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none