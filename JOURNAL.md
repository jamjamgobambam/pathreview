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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix. From PLAN.md: read `hybrid.py`, `keyword_search.py`, and `vector_store.py` to confirm the exact scoring behavior (step 1 done), then added a new "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md` (steps 2–5 done). The section documents the blended formula `blended = vector_weight * norm(vector_score) + keyword_weight * norm(keyword_score)`, the default `0.7` / `0.3` weights, the per-set 0–1 normalization, the `min_score` (0.3) filter and top-`max_chunks` ranking, a worked numeric example, and the edge cases the code already handles. Committed as `docs(rag): document hybrid retrieval scoring formula`.

**Next steps:**
Self-review against CONTRIBUTING.md (done), then open the PR against pathreview using the template, request peer/mentor feedback, and finalize.

**Blockers:**
None on the fix itself. This is a documentation-only issue, so there is no application code to unit-test — the change adds no new tests by design.

---

### Check-in 2 (end of week)

**PR link:** _[to be added when the PR is opened]_

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**
A new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md` that explains how `HybridRetriever.retrieve()` combines vector similarity and BM25 keyword scores: normalize each score set to 0–1, blend with default weights of 0.7 (vector) and 0.3 (keyword), filter by a 0.3 `min_score`, and return the top `max_chunks`. Includes a worked numeric example and documents single-searcher, empty-set, and all-filtered edge cases. No runtime behavior was changed.

**Tests added or updated:**
None. This is a documentation-only change to `docs/ARCHITECTURE.md`, which is not covered by unit tests. No source code was modified, so no tests were added or updated.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Note on pre-existing failures: before making any change, `make check` reported 182 ruff errors and `make test-unit` reported 53 failed / 375 passed. These failures are all in pre-existing Python source and test files (e.g. `test_pii_scrubber.py`, `test_review_service.py`, `test_resume_parser.py`, `test_tech_detector.py`) and are unrelated to this issue. My change touches only `docs/ARCHITECTURE.md` (zero Python), so it introduces no new failures — the pre-commit hooks confirm no Python files were checked. Per the Week 9 guidance, "passes" here means my changes introduce no new failures.

**Draft PR feedback received from:** _[name or Slack handle, or "none"]_
