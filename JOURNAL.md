## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [Y] Tier 3

**Problem summary:**
Currently, chunks are retrieved and ranked based on a hybrid approach, using semantic and keyword search. However, this ranking is not in the perfect order, for example because keyword search might rank a document higher just because it contains a specific keyword multiple times. Hence, the need for re-ranking.

**Branch name:** feat/34-re-ranking-chunks

**Setup confirmation:** [Y] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]
https://github.com/Phuc1Le/pathreview/commit/c5c9db5
This first commit is to fix another issue, keyword_score is always 0, which was reproduced and fix-verified with tests/unit/test_hybrid.py
https://github.com/Phuc1Le/pathreview/commit/81ea29f
This is the reproduction of issue #34
**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I created a mock vector store with mock chunks, 2 of which are actual relevant chunk and keyword-stuffed chunk. Without the re ranker, the stuffed chunk score is higher than the actual relevant chunk.
**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are done: (1) implemented `Reranker` in `rag/retriever/reranker.py`
using an LLM call to score candidate chunks, with defensive parsing and fallback to the
existing blended score on any failure; (2) added `tests/unit/test_reranker.py` proving it in
isolation, including that it corrects the exact keyword-stuffing bias `test_hybrid_keyword_bias.py`
showcased; (3) widened `HybridRetriever`'s candidate pool (`candidate_multiplier`) and wired
`Reranker` into `retrieve()` as an optional, opt-in dependency so existing behavior is unchanged
when no reranker is configured; (4) added `tests/unit/test_hybrid_with_reranker.py` proving the
fix end-to-end (retriever + reranker together flip the "stuffed" vs "relevant" ranking).

**Next steps:**
Open a PR, get it reviewed, and consider tightening the LLM's structured-output enforcement
(currently relies on prompt instructions + regex fallback, not the API's native JSON mode).

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/Phuc1Le/pathreview/pull/1)

**Branch:** feat/34-re-ranking-chunks

**What you built:**
An LLM-based re-ranking step (`rag/retriever/reranker.py`) that sits downstream of
`HybridRetriever`'s vector/keyword blend. `HybridRetriever` now optionally accepts a `Reranker`
and, when configured, widens its candidate pool before handing it to the LLM for final scoring
and ordering, correcting cases where keyword repetition previously outranked genuinely relevant
chunks. Falls back gracefully to the original blended-score order if the LLM call fails or
returns unparseable output.

**Tests added or updated:**
- `tests/unit/test_hybrid.py` — reproduces and confirms the fix for a separate, blocking bug
  found along the way (`keyword_score` always 0.0, because `KeywordSearcher` was never indexed).
- `tests/unit/test_hybrid_keyword_bias.py` — showcases issue #34 itself: without a reranker, a
  keyword-stuffed but off-topic chunk outranks a genuinely relevant one.
- `tests/unit/test_reranker.py` — unit tests for `Reranker` in isolation (mocked LLM client):
  empty input, correcting the keyword-stuffing bias, `top_k` truncation, and three fallback
  paths (LLM error, malformed output, partially-scored response).
- `tests/unit/test_hybrid_with_reranker.py` — end-to-end: `HybridRetriever` + `Reranker` wired
  together actually flip the ranking, plus a sanity check that the bias still reproduces without
  a reranker configured (isolating that the fix, not some other change, is what flips it).

**Self-review confirmation:** [x] make check passes*  [x] make test-unit passes*

*Scoped to files touched for this issue: `ruff`/`black` clean on `rag/retriever/` and the four
test files above; `mypy` unverifiable directly in this environment (blocked by a local
Application Control policy) but passes via the pre-commit hook used for every commit.
`test-unit` full-suite run: 386 passed, 53 failed — all 53 failures are pre-existing, in files
unrelated to this issue (e.g. `test_pii_scrubber.py`, `test_review_service.py`,
`test_resume_parser.py`); none of the 11 tests added/touched for issue #34 are among them.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No reviewer came in yet

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
There were issues that were non-related to mine, but I had to fix them in order for mine to work
**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
Every changes must be cocumented clearly, otherwise it'll be hard for other people to understand and navigate the codebase. Also I learn to make sure that my changes don't affect other components via testing.
**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI's still great at writing the code. This time it even helped me point out relevant issues I needed to fix aside from mine.
**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I guess not. I implemented a good new feature, tested it, and created a PR. Maybe I'd start sooner if I were to do it again. That way I'd have more time to write the code myself, instead of letting Claude do most of the work and check later on.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
Reading and following the documentations to maintain a proper, professional workfloww