## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` explained that hybrid retrieval is based on vector similarity and BM25 keyword but does not include the scoring formula. The documentation lacked the formula and the default weights. Without such details, contributors and reviewers of retrieval changes cannot understand how ranking behaves without reverse-engineering the code.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is This Issue Right for Me?" checklist reasoning:**

### Part 1 — Understanding the Issue

[x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.

[x] I've located the relevant files and confirmed they exist in the codebase.

I located the affected places and confirmed they exist:

* `docs/ARCHITECTURE.md`
* `rag/retriever/hybrid.py`

[x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

Before the fix the doc lakcs scoring detail. After the fix, it has a section a reader can use to understand hybrid retrieval scoring.

### Part 2 — Tier Fit

[x] If this is my first open source contribution: I'm choosing Tier 1.

This is my first contribution to this codebase, so I followed the guidance and chose Tier 1.

### Part 3 — Codebase Readiness

[x] I've found and read the specific code the issue references (not just the file — the function or section).

[x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.

[Not Applicable] I've found the test file for my module and read at least one test end-to-end.

I confirmed the gap is real by reading `docs/ARCHITECTURE.md` and `HybridRetriever.retrieve()` in `rag/retriever/hybrid.py`.

### Part 4 — Scope and Time

[x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.

[x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.

[x] This issue has no open blockers or dependencies on other unresolved issues.

I was the first one to claim this issue. The issue estimates 2 to 3 hours, which fits comfortably in the Weeks 8 to 9 window alongside my other commitments. I checked the issue for blockers and dependencies and found none, and I reviewed the existing claims on the issue before claiming it myself.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/mitechzone/pathreview/commit/1fbe32739f50bc8a08fd4b15035cdafc51ea6c76

**Reproduction summary:**
I confirmed the issue directly against the codebase during issue selection.

Current `docs/ARCHITECTURE.md` covers hybrid retrieval with no formula, no weights, and no example, while `rag/retriever/hybrid.py` implements a weighted scoring blend that is documented nowhere in `docs/`.

Running the app is not applicable to reproducing a documentation gap. The reproduction is the side-by-side reading of the doc section and the retriever code.

**PLAN.md link:**
https://github.com/mitechzone/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md

**Walkthrough video (recommended):**
Unnecessary for missing documentation.

**Blockers or open questions:**
No.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

All four sub-tasks from PLAN.md are complete. I drafted the "Hybrid Retrieval Scoring" subsection under "RAG System" in `docs/ARCHITECTURE.md` (formula, default weights, normalization, min-score filtering), added a worked example with three chunks and verified its arithmetic by hand, cross-checked every statement sentence by sentence against `HybridRetriever.retrieve()`, and did a grammar and format consistency pass.

The change is committed as `docs(rag): explain hybrid retrieval scoring formula` and pushed.

I also ran `make check` and `make test-unit` before and after the change: identical results as expected, confirming my docs-only change introduces no new failures.

**Next steps:**

Open a draft PR to the upstream repository, share it for peer feedback in Slack, address any feedback, then mark the PR ready for review and complete Check-in 2.

**Blockers:**

None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/424

**Branch:** docs/36-hybrid-retrieval-scoring-formula

**What you built:**
A "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md` that documents how `HybridRetriever` ranks chunks: per-method max-normalization, the weighted blend formula with the 0.7/0.3 constructor defaults, the minimum-score filter, and a worked three-chunk example with hand-verified arithmetic. It closes issue #36, where the scoring logic existed only in source code.

**Tests added or updated:**
Not applicable. This is a docs-only change: it touches only Markdown, alters no code paths, and there is no test framework for prose. I was advised by the instructor and tech fellows (TFs) that for docs-only changes new test cases are not applicable and none are required. Explicitly documenting this, as done here and in the PR, qualifies for full credit on the relevant rubric items. Correctness was verified instead by cross-checking every statement against `HybridRetriever.retrieve()` and recomputing the example arithmetic by hand.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both commands were run before and after the change with identical results. Per the module guidance on codebases with documented pre-existing failures, "passes" means my change introduces no new failures, which the identical before/after outputs confirm.

**Draft PR feedback received from:** none
