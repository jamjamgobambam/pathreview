\## Week 7 — Issue Selection



\*\*Issue link:\*\* https://github.com/ascherj/pathreview/issues/36



\*\*Issue title:\*\* Architecture doc doesn't explain the hybrid retrieval scoring formula



\*\*Tier:\*\* \[x] Tier 1  \[ ] Tier 2  \[ ] Tier 3



\*\*Problem summary:\*\*

The architecture documentation explains that hybrid retrieval combines vector similarity and keyword relevance, but it does not show how those scores are mathematically combined. It also does not identify the default weights used by the system, making the retrieval process harder for contributors to understand or reproduce. This issue affects `docs/ARCHITECTURE.md` and does not require changing the application's runtime behavior. A successful fix will document the scoring formula, state the default weights, and include a clear worked example.



\*\*Selection reasoning:\*\*

I selected this issue because it is a Tier 1 task with a clearly defined and manageable scope. The work is limited to one documentation file, and I can inspect the existing retrieval code to confirm the formula and weights before writing the explanation. It does not require redesigning the application or modifying several unrelated modules. This makes it appropriate for my current experience while still requiring me to understand how the hybrid retrieval system works.



\*\*Branch name:\*\* `docs/36-hybrid-retrieval-scoring`



\*\*Setup confirmation:\*\* \[x] App runs locally at localhost:5173



\*\*Cohort ledger:\*\* \[x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/mattmiara04/pathreview/commit/4b8bfce

**Reproduction summary:**  
I reproduced issue #36 by comparing `docs/ARCHITECTURE.md` with the hybrid retrieval implementation in `rag/retriever/hybrid.py`. The architecture document only states that hybrid retrieval combines vector similarity and BM25 keyword search, while the implementation normalizes both scores, applies default weights of 0.7 and 0.3, calculates a blended score, filters by a minimum score, and sorts the remaining results.

**PLAN.md link:** https://github.com/mattmiara04/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**  
I need to ensure the documentation explains the scoring behavior accurately without making the architecture section unnecessarily difficult to understand.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**  
I reviewed the hybrid retrieval implementation and completed the documentation update described in `PLAN.md`. I added the scoring formulas, default weights, threshold behavior, ranking process, worked example, and edge-case behavior to `docs/ARCHITECTURE.md`.

**Next steps:**  
Add and run a focused test for the architecture documentation, complete the repository checks, open the pull request, and document the final results.

**Blockers:**  
The repository has pre-existing Ruff, Black, Mypy, and unit-test failures unrelated to Issue #36.

---

### Check-in 2 (end of week)

**PR link:** [PASTE_PR_URL_HERE](https://github.com/ascherj/pathreview/pull/726)

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**  
I updated the architecture documentation to explain how vector similarity and BM25 scores are normalized and combined using the default 0.7/0.3 weighting formula. I also documented threshold filtering, ranking, missing-result behavior, and added a worked scoring example.

**Tests added or updated:**  
Added `tests/unit/test_architecture_docs.py`. It verifies that `docs/ARCHITECTURE.md` includes the hybrid scoring section, normalized score names, blended formula, default weights, minimum threshold, and missing-result behavior.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

The repository contains documented pre-existing failures, but the same failures remained before and after my contribution. The unit-test result improved from 375 passing tests to 376 passing tests while remaining at 53 failures, confirming that the new test passed and no new failures were introduced.

**Draft PR feedback received from:** none