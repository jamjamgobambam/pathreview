## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/36]

**Issue title:** [Architecture doc doesn't explain the hybrid retrieval scoring formula #36]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue of ARCHITECTURE.md is that its description of the hybrid retrieval is too vague. It doesn't provide additional details regarding how the hybrid retrieval scores its chunks. Updating this file provides more clarity and context of rag/retriever/hybrid.py for contributors in the repository who are working on the RAG, especially the hybridg retrieval system.

**Branch name:** docs/36-update-architecture

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** The issue regarding missing details of the hybrid retrieval score in ARCHITECTURE.md exists in my local environment. Because it is documentation, I don't need to reproduce the issue by code. 

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** https://raw.githubusercontent.com/unsunnysideup/pathreview/refs/heads/docs/36-update-architecture/docs/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The following subtasks are complete. No coding commits is needed; just comprehension of the root issue and files needed for the revision:
1. Understanding where in the ARCHITECTURE.md I need to revise and add resolution to the issue
2. Read and understand the hybrid retrieval scoring formula in rag/retriever/hybrid.py

**Next steps:**
I will complete the last two steps I've outlined in PLAN.md
3. Write a cohesive and concise statement about the hybrid retrieval scoring formula in ARCHITECTURE.md
4. Proofread and submit

---

### Check-in 2 (end of week)

**PR link:** [link to the submitted pull request](https://github.com/ascherj/pathreview/pull/788)

**Branch:** docs/36-update-architecture

**What you built:**
I added a subsection under "subsystem details" -> "Rag System" (Hybrid Retrieval Scoring Logic) which details the scoring logic for the retrieval system. There were two subsections under that section detailing the normalization process as well as what would happen if a chunk is missing from a vector or keyword evaluation set. 

**Tests added or updated:**
No tests were added as this was a documentation revision. 

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** None