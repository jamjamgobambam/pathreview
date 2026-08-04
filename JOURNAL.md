## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula
 #36

**Tier:** [y] Tier 1  [ ] Tier 2  [ ] Tier 3

**Tier reasoning:** I chose tier 1 since this is my first time contributing to a large codebase.

**Problem summary:**
Issue #36 is about a documentation gap in docs/ARCHITECTURE.md. The RAG System section (line 60) states that hybrid retrieval "blends" vector similarity and BM25 keyword scores, but it stops at naming the two signals — it never says how they're combined. 
Concretely, there's no formula showing how the two scores are normalized and merged, no statement of the default weighting between them, and no worked example showing a document's final rank being computed. 
A successful fix adds a subsection to the doc that spells out the scoring formula, states the default weights, and walks through a small example so contributors understand and can adjust the retrieval behavior.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [y] App runs locally at localhost:5173

**Cohort ledger:** [y] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sarah-yiyang/pathreview/commit/c3c05df421bb35efe96f622a8a9c4d3ec647410a

**Reproduction summary:**
I opened docs/ARCHITECTURE.md and read the RAG System section, which describes hybrid retrieval as "blending" vector similarity and BM25 keyword scores. I confirmed the gap: the doc names the two signals but never gives the scoring formula, the default weighting, or a worked example, so there's no way to tell how a document's final rank is actually computed.

**PLAN.md link:** https://github.com/sarah-yiyang/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md

**Blockers or open questions:**
N/A

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
* Implemented the fix: traced the scoring logic in `rag/retriever/hybrid.py` (the `HybridRetriever.retrieve` method) and added a new "Hybrid retrieval scoring" subsection to the RAG System section of `docs/ARCHITECTURE.md`.
* The new subsection documents everything the issue said was missing: the per-set max normalization step, the weighted-sum formula, the default weights (`vector_weight=0.7`, `keyword_weight=0.3`) and that they're tunable, the missing-signal/division-by-zero edge cases, and a worked example computing a chunk's final rank.

**Next steps:**
* Open the PR from `docs/36-hybrid-retrieval-scoring-formula` against upstream and fill in each required section with substantive content — Summary (what the doc gap was), Issue (link #36), Changes (the new subsection in `docs/ARCHITECTURE.md`), Testing (how I verified the formula against the code), and Notes for Reviewers (that this is docs-only, no behavior change).
* Verify the formula in the doc once more against `hybrid.py` before submitting, and run `make check` so the PR passes CI.

**Blockers:**
* This is a documentation-only change, so there's no code change that strictly requires a test. The one optional addition would be a regression test for `HybridRetriever` (there isn't one today) that pins the documented formula — I'll decide whether to include it before submitting rather than treating it as a blocker.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/816)

**Branch:** (https://github.com/sarah-yiyang/pathreview/tree/docs/36-hybrid-retrieval-scoring-formula)

**What you built:**
I added a "Hybrid retrieval scoring" subsection to the RAG System section of `docs/ARCHITECTURE.md`, documenting how `HybridRetriever` (`rag/retriever/hybrid.py`) actually combines its two signals. The subsection spells out the per-set max normalization of the vector and BM25 scores, the weighted-sum formula (`blended_score = vector_weight * norm_vector + keyword_weight * norm_keyword`), the default weights (`vector_weight = 0.7`, `keyword_weight = 0.3`) and that they are constructor-tunable, the edge cases (chunks are unioned across both result sets so a missing signal contributes `0`, and an empty result set's max is treated as `1.0` to avoid division by zero), the `min_score = 0.3` / `max_chunks = 10` post-filtering, and a worked example computing two chunks' final ranks. 

**Tests added or updated:**
None — this is a documentation-only change, so no source behavior was modified and no test file was touched. I considered adding a regression test for `HybridRetriever` to pin the documented formula (there isn't one today), but decided that belongs in a separate code-change PR rather than bundled into a docs fix.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
