## Week 7 – Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The architecture documentation says that hybrid retrieval combines vector and keyword search scores, but it does not explain the formula used to combine them. It also does not provide the default weights or an example calculation. A successful fix will add a clear section to `docs/ARCHITECTURE.md` explaining the scoring formula, the weights, and a simple example. This will help contributors understand how search results are ranked.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/dfb3e54db650ace92c2b59103e4409572aad096a)

**Reproduction summary:**
I reviewed the RAG System section in `docs/ARCHITECTURE.md` and confirmed that it only states that vector similarity and BM25 keyword retrieval are combined. I then traced the implementation to `rag/hybrid.py`, where the scores are normalized and blended using default weights of 0.7 for vector similarity and 0.3 for BM25 relevance, none of which is currently documented.

**PLAN.md link:** (https://github.com/kennedypham108/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md)

**Walkthrough video (recommended):** Not completed

**Blockers or open questions:**
I still need to verify the exact default scoring weights and score normalization behavior from the hybrid retrieval implementation.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reviewed the hybrid retrieval implementation and completed the documentation task from `PLAN.md`. I updated `docs/ARCHITECTURE.md` to explain the normalized weighted scoring formula, the default vector and keyword weights, a numerical scoring example, and how the final results are filtered and ranked.

**Next steps:**
I will run `make check` and `make test-unit`, review the documentation against the implementation, open a draft pull request, and request feedback from a classmate or mentor.

**Blockers:**
None currently.

---
### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/937)

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**
I updated `docs/ARCHITECTURE.md` to explain how hybrid retrieval combines normalized vector similarity and BM25 keyword scores. The documentation now includes the weighted scoring formula, the default weights, a worked numerical example, and an explanation of how the results are filtered and ranked.

**Tests added or updated:**
No tests were added or updated because this was a documentation-only change and did not modify application behavior. I ran the existing unit test suite. It completed with 375 passing tests and 53 pre-existing failures in unrelated modules, including resume parsing, review services, security, skill extraction, structural chunking, and technology detection. My changes did not introduce new test failures.

**Self-review confirmation:** [ ] `make check` passes  [ ] `make test-unit` passes

`make test-unit` currently reports 375 passed, 53 failed, and 1 warning. The failures are in unrelated existing modules and are not caused by this documentation-only change. This PR only modifies `docs/ARCHITECTURE.md`.

**Draft PR feedback received from:** None for right now


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided. For Summer 2026, reviewer feedback is not part of the contribution process, so I did not receive any comments or requested changes on my PR.

**How you responded:**
No response or additional changes were needed because no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**
The hardest part was understanding how the existing codebase worked before making my contribution. My issue sounded simple because I only needed to document the hybrid retrieval scoring formula, but I still had to trace the implementation in `rag/hybrid.py` and make sure the documentation matched the actual code. I also found the Git and pull request workflow more complicated than expected, especially keeping track of my branch, commits, tests, and the required journal check-ins.

**What did you learn about working in a large codebase?**
I learned that contributing to an existing codebase requires more investigation before making changes. In my own projects, I usually already know why the code was written a certain way, but in someone else's project I had to read nearby files and understand the existing structure before changing anything. I also learned that even a documentation issue should be based directly on the implementation. For example, I verified that hybrid retrieval uses a default weight of 0.7 for vector similarity and 0.3 for keyword relevance before documenting the formula and example.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for helping me understand unfamiliar code, break the issue into smaller steps, explain Git commands, and review the wording of my documentation. They also helped me understand how the hybrid scoring calculation worked. However, I still had to inspect the actual repository and run the commands and tests myself. AI could suggest what the code probably did or what command I should use, but I needed to verify that those suggestions matched my specific repository and the assignment requirements.

**What would you do differently if you started over?**
If I started over, I would organize the contribution process more carefully from the beginning. I would keep `JOURNAL.md` updated after every major step instead of returning to it later, and I would record my branch name, test results, commit information, and PR link as soon as I created them. I would also spend more time reading the relevant implementation before writing my plan so that I could understand the issue and edge cases earlier.

**What are you most proud of from this module?**
I am most proud that I was able to take a small issue in an unfamiliar repository, trace the actual implementation, and turn it into clearer documentation. I documented the hybrid retrieval scoring formula, the default 0.7 vector and 0.3 keyword weights, and included a numerical example so that future readers can understand how the final retrieval score is calculated.
