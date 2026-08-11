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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**  
No reviewer feedback was received. The Summer 2026 course notes stated that reviewer feedback was not being provided during this term, so I documented that no review came in.

**How you responded:**  
No changes were required in response to reviewer feedback because none was received.

---

### Reflection

**What was harder than you expected?**  
The hardest part was navigating a large unfamiliar codebase and figuring out where the actual hybrid retrieval behavior was implemented. At first, searches returned unrelated scoring code and files inside `.venv` and `node_modules`, so I had to narrow the search until I found `rag/retriever/hybrid.py` and compare it directly with `docs/ARCHITECTURE.md`.

**What did you learn about working in a large codebase?**  
I learned that contributing to an existing project requires understanding how multiple files work together before making even a small change. For Issue #36, I had to trace the behavior across `rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`, `rag/retriever/keyword_search.py`, and `docs/ARCHITECTURE.md` instead of assuming the documentation alone described the full system.

**How did AI tools help — and where did they fall short?**  
AI tools helped me navigate the repository, narrow down searches, understand the hybrid scoring formula, create a solution plan, and structure the documentation and test. However, I still had to verify the suggestions against the real code, especially when early searches returned unrelated files and when the repository had many pre-existing Ruff, Mypy, formatting, and unit-test failures.

**What would you do differently if you started over?**  
I would inspect the project structure and exclude folders such as `.venv` and `node_modules` from searches immediately. I would also run the baseline tests and validation checks earlier so I could separate pre-existing failures from anything caused by my contribution before starting the implementation.

**What are you most proud of from this module?**  
I am most proud that I was able to take Issue #36 from initial investigation through planning, implementation, testing, and a real pull request. I documented the hybrid retrieval scoring process, including the 0.7 vector and 0.3 BM25 weighting, added a focused test for the architecture documentation, and confirmed that my work did not introduce new test failures.