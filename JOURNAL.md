# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `docs/ARCHITECTURE.md` file mentions that the retrieval system blends vector search and keyword search scores, but it never explains how that blend is actually calculated or what the default weighting is. Right now a reader has no way to know how much each score contributes to the final ranking, or to reproduce it by hand. A successful fix adds a clear section explaining the scoring formula, the default weights, and a worked example so future contributors can understand and tune the retrieval logic. This affects the retrieval/RAG portion of the codebase.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Issue Selection Checklist Reasoning

**Part 1 — Understanding:** The issue is that ARCHITECTURE.md mentions hybrid
retrieval blends vector and keyword scores, but never explains the formula or
default weights. I confirmed this by reading the current doc section and found
it's a one-line description with no math. I then found the actual
implementation in rag/retriever/hybrid.py: it's a weighted sum of normalized
vector and BM25 scores (default weights 0.7 vector / 0.3 keyword), where each
score is divided by the max score in its own result set before blending.
Done = a new doc section explaining this formula, the default weights, and a
worked numeric example.

**Part 2 — Tier fit:** This is my first pathreview contribution, so Tier 1 is
the right starting point regardless of my prior RAG experience — the goal
here is learning the contribution workflow, not testing my RAG knowledge.

**Part 3 — Codebase readiness:** Found and read rag/retriever/hybrid.py in
full, including the retrieve() method and score normalization logic. This is
a docs-only issue so there's no test file to modify, but I confirmed the
scoring behavior directly from the source rather than guessing from the
issue description.

**Part 4 — Scope and time:** Several other students have also claimed issue
#36 in the comments (at least 10+ across multiple AI-201 sections). Claims
are non-exclusive per the checklist, and my grade is based on my own
artifacts, so I'm comfortable proceeding despite the overlap. Estimated time:
2-3 hours as labeled, and I've already done the code investigation, so this
is realistic for Weeks 8-9. No blockers or dependencies mentioned on the issue.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/anamgiri91/pathreview/commit/2b9974a

**Reproduction summary:**
I wrote a test suite (`tests/unit/test_hybrid_retriever.py`) that mocks `HybridRetriever`'s vector store and keyword searcher, feeds in known raw scores, and asserts the blended output matches a hand-calculated formula: `blended = vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score`, with each score normalized against the max in its own result set. All 4 tests passed on the first correct run, confirming my Week 7 read of `rag/retriever/hybrid.py` was accurate, and that this behavior is genuinely undocumented in `docs/ARCHITECTURE.md`.

**PLAN.md link:** https://github.com/anamgiri91/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md

**Walkthrough video (recommended):** N/A — did not record one this week.

**Blockers or open questions:**
The repo's pre-commit hooks (`ruff`, `black`, `mypy`) fail on pre-existing, unrelated type-annotation gaps in `rag/retriever/keyword_search.py` and `rag/retriever/vector_store.py`. This blocked committing my reproduction test through normal hooks and required `git commit --no-verify` for both commits this week. Not something I plan to fix myself since it's out of scope for a docs-only issue, but I've flagged it in `PLAN.md`'s risks section in case a maintainer wants it addressed separately.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the core implementation for issue #36: added a new "Hybrid Retrieval Scoring" section to `docs/ARCHITECTURE.md` explaining the blending formula, default weights (0.7 vector / 0.3 keyword), per-result-set normalization, and a worked numeric example. This satisfies sub-tasks 1-4 from PLAN.md. Also confirmed via `make check` and `make test-unit` that the codebase has 182 pre-existing lint errors and 53 pre-existing test failures, none in files I touched — my reproduction test (`tests/unit/test_hybrid_retriever.py`) passes cleanly and introduces no new failures.

**Next steps:**
Cross-reference the reproduction test file directly in the PR description (sub-task 5 from PLAN.md, already partially done in the doc itself). Self-review against `docs/CONTRIBUTING.md` conventions before opening the PR, and request peer/mentor feedback in Slack on a draft PR.

**Blockers:**
None currently. The pre-commit hooks in this repo fail on unrelated pre-existing type-annotation gaps (noted in PLAN.md's risks section), so I've been using `git commit --no-verify` for my commits — worth double-checking with a mentor whether that's the expected workaround or if there's a preferred approach in this cohort.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/724

**Branch:** docs/36-hybrid-retrieval-scoring-formula

**What you built:**
Added a "Hybrid Retrieval Scoring" section to `docs/ARCHITECTURE.md` documenting the previously-unexplained blending formula, default weights (0.7 vector / 0.3 keyword), per-result-set normalization, and a worked numeric example.

**Tests added or updated:**
Created `tests/unit/test_hybrid_retriever.py` with 4 tests: confirms the default weight values, confirms the blended score matches a hand-calculated example across 4 sample chunks, confirms normalization is computed per-result-set (not globally), and confirms a chunk needs to appear in only one of the two result sets to receive a score.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(182 pre-existing lint errors and 53 pre-existing test failures confirmed unchanged before/after my changes — see PR description for full baseline. My changes introduce no new failures.)

**Draft PR feedback received from:** none — posted for review but did not receive feedback before the deadline

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in. Per the Su26 cohort note, reviewer feedback isn't a feature this term, so I didn't expect any beyond what I requested informally.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
The hardest part ended up being Git, not the documentation itself. I ran into several issues while rewriting commit messages with interactive rebase. At one point I accidentally merged lines while editing the rebase todo list in vim. Later, I had a rebase complete successfully, only to discover that it had silently dropped a WatchlistEntry model because there wasn't any overlapping code for Git to mark as a conflict. I also spent more time than expected dealing with terminal issues, especially when trying to paste multi-line markdown tables with pipe characters, since the shell kept interpreting them incorrectly. The actual documentation work wasn't the difficult part—it was all the tooling around it.

**What did you learn about working in a large codebase?**
One of the biggest lessons I learned is that a successful rebase doesn't necessarily mean everything is still correct. Git only reports conflicts when the same lines overlap, so code can disappear without any warning if it only exists on one branch. I only caught the missing class because I ran the test suite immediately after rebasing instead of assuming everything was fine. I also learned that in a large, established project, there will often be existing lint or test failures that aren't related to your work. Instead of trying to fix everything, it's more important to establish a baseline before making changes so you can show that your work didn't introduce any new problems.

**How did AI tools help — and where did they fall short?**
AI was most helpful for challenging my own thinking. Asking it for counterarguments to my design decisions helped me notice weaknesses I probably would have overlooked otherwise. It also sped up writing the reproduction test by helping generate mocked scenarios and verify the expected results. Where it wasn't as helpful was troubleshooting terminal and Git issues. Things like vim editing, shell escaping, heredocs, and rebase problems depended heavily on what was happening in my local environment, so they usually required several rounds of trial and error instead of a single solution.

**What would you do differently if you started over?**
I spent a lot of time just trying to understand the codebase before I felt comfortable making any changes. Most of that time went into tracing through files like hybrid.py, understanding the retriever's normalization logic, and figuring out how everything fit together. If I started over, I'd use AI more during that learning phase. Instead of reading every file line by line first, I'd ask it to explain unfamiliar functions, summarize what different files were responsible for, and point out which sections were actually relevant to my issue. I mainly used AI to critique my ideas and help with testing, but I think I could have saved a lot of time by using it more to understand the codebase itself.

**What are you most proud of from this module?**
I'm most proud of noticing that _get_all_chunks() in HybridRetriever.retrieve() fetches every chunk but never actually uses the result. That wasn't something I was looking for—I found it by carefully reading through the implementation while writing the documentation. It was satisfying to understand the code well enough to catch a detail like that instead of just describing the feature at a high level.