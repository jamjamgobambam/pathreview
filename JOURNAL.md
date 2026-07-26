## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36
**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3 <!-- Put an x in the correct bracket -->

**Problem summary:**
docs/ARCHITECTURE.md contains a high level explanation of hybrid retrieval and how it's incorporated in this project, but doesn't explain the formula or the default wiehgts. A successful fix would be going more in depth in how the hybrid retrieval process works, and adding a section explaining the scoring logic. An example should also be included.
[Write 3–5 sentences in your own words explaining what is broken or missing, what a successful fix looks like, and which part of the codebase it touches.]

**"Is this right for me?" Reasoning:**
This issue is right for me because I have never worked on an open source issue. This issue was labeled with tier 1 and good first issue, so it seemed like a good option. I also want to learn more in depth about hybrid retrieval, so completely this issue allows me to get more experience with that topic.

[Briefly state your scope reasoning here based on the checklist guidelines.]

**Branch name:** `docs/36-hybrid-retrieval-scoring`
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproducing the Issue:** confirmed ARCHITECTURE.md line 60 mentions hybrid retrieval but doesn't outline or explain the formula defined in hybrid.py:78-81

**Reproduction commit link:** https://github.com/cullan-wick/pathreview/commit/aeb4391

**Reproduction summary:**
Since this is a documentation gap rather than a runtime bug, I reproduced it by tracing the doc against the code: `docs/ARCHITECTURE.md` line 60 only says "hybrid retrieval (vector similarity + BM25 keyword)," while the actual scoring formula, default weights (0.7 / 0.3), 0–1 normalization, and `min_score` filter all live in `rag/retriever/hybrid.py` (lines 14, 58–59, 78–81, 92–97). I confirmed the doc gives a reader no way to understand the scoring without opening the source.

**PLAN.md link:** https://github.com/cullan-wick/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
