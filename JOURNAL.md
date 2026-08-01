# JOURNAL

A running record of progress throughout Module 3. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` mentions that the RAG system uses hybrid retrieval blending
vector similarity and BM25 keyword scores, but it never explains how those scores are
actually combined. There is no description of the default weights, no explanation of how
each score is normalized, and no worked example, so a contributor cannot understand or
tune the ranking behavior from the docs alone. The scoring logic lives in
`rag/retriever/hybrid.py` (`HybridRetriever.retrieve()`), which normalizes each modality
to 0–1 and blends them with a 0.7 vector / 0.3 keyword weighting. A successful fix adds a
"Hybrid Retrieval Scoring" section to `docs/ARCHITECTURE.md` covering the formula, the
default weights, normalization, a numerical example, and relevant edge cases.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tsunderii/pathreview/commit/df02de1f375ef22545b7e89f2e7e3ac589101118

**Reproduction summary:**
Because this is a documentation gap (not a runtime bug), I reproduced it by confirming
the formula is absent from the docs while it exists in code: `grep -in
"weight|normali|bm25|blend|formula|min_score" docs/ARCHITECTURE.md` returns only the
single one-line mention at line 60 (no weights, no normalization, no example), whereas the
actual blending lives in `rag/retriever/hybrid.py:58-81`. I then reproduced the scoring
math by re-implementing lines 58–81 in a standalone script over a sample candidate set and
observed the exact blended scores I plan to document (A=1.000, C=0.500, B=0.467; D=0.075
dropped by the default `min_score=0.3`), confirming I understand precisely what is missing
and where it belongs.

**PLAN.md link:** https://github.com/tsunderii/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
- Two adjacent code observations may be out of scope for a docs-only fix but are worth
  flagging in the PR: (a) `retrieve()` fetches `all_chunks` at hybrid.py:50 but never calls
  `keyword_searcher.index(...)`, so the keyword arm can be empty; (b) the similarity comment
  at vector_store.py:102 says "euclidean" while the collection is created with cosine space
  (vector_store.py:36). I plan to document intended behavior and note these separately rather
  than fix code in this issue.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. Sub-tasks 1–4 are done: added a `#### Hybrid Retrieval
Scoring` subsection to `docs/ARCHITECTURE.md` under the RAG System section, containing the
blended-score formula, the default 0.7/0.3 weights table, the max-normalization explanation
for vector similarity and BM25, the worked numerical example (validated in Week 8), and a
notes/edge-cases list. Committed as `docs(rag): document hybrid retrieval scoring formula`.

**Next steps:**
Finish sub-task 5: run `make check` and `make test-unit` to record the baseline, fill in
the PR template, and open the PR against upstream `main`. Then add the PR link to Check-in 2.

**Blockers:**
None blocking. Noted that the repo has pre-existing `make check`/`make test-unit` failures
unrelated to this change (see Check-in 2); since this PR is documentation-only it introduces
no new failures.

---

### Check-in 2 (end of week)

**PR link:** _(to be filled when the PR is opened)_

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**
A documentation-only change that adds a "Hybrid Retrieval Scoring" section to
`docs/ARCHITECTURE.md`. It explains how `HybridRetriever.retrieve()` blends vector and BM25
scores (`blended = 0.7·norm_vector + 0.3·norm_keyword`), how each score is max-normalized to
0–1, and walks through a numerical example, plus edge cases such as the `min_score` threshold.

**Tests added or updated:**
None — this is a documentation-only change (no Python touched), so no unit tests apply. Ran
the existing suite to confirm no regressions.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

> "Passes" here follows the course rule for a codebase with documented pre-existing failures:
> **this change introduces no new failures.** Baselines observed before my change (all in
> Python/config files this branch does not touch): `make test-unit` = 53 failed / 375 passed;
> `ruff check .` = 182 errors; `black --check .` = 52 files; `mypy` = 5 errors. After my
> markdown-only change the numbers are identical (0 new failures); this branch modifies only
> `.md` files, which none of these tools inspect.

**Draft PR feedback received from:** none
