## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36
**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `docs/ARCHITECTURE.md` file currently describes that the RAG subsystem performs hybrid retrieval by blending vector similarity and keyword search results, but it does not specify how this blending is calculated. Specifically, it lacks details on the mathematical formula used to combine the scores, the default weights applied to each search method, and how the scores are normalized. A successful fix will add a detailed section to `docs/ARCHITECTURE.md` explaining this scoring process, detailing the default weights of 0.7 for vector and 0.3 for keyword searches, and providing a step-by-step example of how the blended score is computed for a document chunk.

**Branch name:** docs/36-explain-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
- **Initial Observation & Motivation**: While logging in as 'user2@example.com', I noticed a UX discrepancy where category confidence scores were displayed as 76%, 81%, 69% next to their respective section names in the feedback section of the frontend, which conflicts with the 58/100 overall evaluation score. Searching for "score" issues in the backlog led me to Issue #36, with similar relation.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Le-Zu/pathreview/commit/8d302fc

**Reproduction summary:**
Inspected `docs/ARCHITECTURE.md` and confirmed that while it mentions hybrid retrieval (vector similarity + BM25 keyword search), it completely omits the mathematical formula, default weights (0.7 vector / 0.3 keyword), score max-normalization logic (`raw_score / max_score`), min_score filtering threshold (0.3), and concrete worked examples implemented in `rag/retriever/hybrid.py`.

**PLAN.md link:** https://github.com/Le-Zu/pathreview/blob/docs/36-explain-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):** N/A

**Risks & file-specific considerations:**
- `rag/retriever/hybrid.py`: Risk of confusing max-normalization (`raw_score / max_score`) with standard min-max scaling `(score - min)/(max - min)` or softmax. Must ensure documentation accurately captures the exact division-by-max logic and the division-by-zero fallback (`default=1.0`).
- `docs/ARCHITECTURE.md`: Risk of markdown layout disruption or header hierarchy mismatch under `### RAG System (`rag/`)`. Must ensure new documentation flows cleanly within the existing section structure.

**Blockers or open questions:**
None. The code in `rag/retriever/hybrid.py` clearly defines the vector weight (0.7), keyword weight (0.3), max-normalization, and score blending equation, providing all necessary details to document in `docs/ARCHITECTURE.md`.