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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
N/A

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Understanding the codebase was harder than I expected because there were many folders and lengthy code in each file. I had to read the ARCHITECTURE.md and README.md to figure out how to navigate, understand the issue I claimed and revise it. 

**What did you learn about working in a large codebase?**
I learned that working in a large codebase require clear and intentional contributions. This will allow other developers to understand your contribution, and pick it up from there. Additionally, there are varying conventions one must follow while contributing to a large codebase. This experience was different from when I would do my own project because I am the only contributor, so I would know where I left off and what to continue

**How did AI tools help — and where did they fall short?**
AI assistance was most helpful in helping me understand certain code lines. For instance, there were certain lines in rag/retriever/hybrid.py where I was a bit confused on what code snippets. 

**What would you do differently if you started over?**
If I started differently, I would take notes while I work so that the next day, I wouldn't need to have to walk back a bit to figure out where to continue. If I took notes, I can trace back in my notes and continue from there, saving the time to resolve issue. 

**What are you most proud of from this module?**
I am most proud of having the skills to properly contribute to open source projects, such as knowing when to merge and when to debase, as I intend to work on open source projects. 