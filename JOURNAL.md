# PathReview — Module 3 Journal

A running record of my Module 3 contribution work. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG system retrieves context by blending two signals — vector (semantic)
similarity and BM25 keyword relevance — but `docs/ARCHITECTURE.md` only mentions
that this blend happens without explaining how. Readers can't tell how the two
scores are combined, that each is min-max normalized to 0–1 before blending, or
that the defaults weight vector at 0.7 and keyword at 0.3. A successful fix adds
a section to the architecture doc that documents the scoring formula
(`blended = vector_weight * vector_score + keyword_weight * keyword_score`), the
normalization step, the default weights, and the `min_score` cutoff, illustrated
with a worked example. The behavior being documented lives in
`rag/retriever/hybrid.py` (`HybridRetriever`).

**Selection reasoning:**
I chose a Tier 1 issue deliberately for my first contribution. I'm still
building familiarity with this codebase (a multi-service Python + React app),
so a documentation issue lets me learn how the RAG retrieval subsystem actually
works before I attempt behavior-changing code in later weeks — the tier matches
my current comfort level. The scope is well-bounded and a good fit: the fix
touches a single file (`docs/ARCHITECTURE.md`) and requires no changes to
application code, tests, or migrations. The hard part is comprehension, not
engineering — I need to read `rag/retriever/hybrid.py`, understand how the two
scores are normalized, weighted, and thresholded, and then explain it clearly.
That is a self-contained, low-risk task I'm confident I can complete well, while
still giving me a real foothold in the retrieval code I'll build on next week.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/yic04/pathreview/commit/35bb7510657297c45c8c9f46047f67a893ec4388

**Reproduction summary:**
Because this is a documentation gap (not a runtime bug), I reproduced it by
confirming the scoring concepts are absent from the doc while the behavior is
fully implemented in code. Grepping `docs/ARCHITECTURE.md` for every relevant
term (`blended`, `vector_weight`, `keyword_weight`, `0.7`, `normal`, `min_score`,
`formula`) returns zero scoring-related hits — the lone `0.3` match is `ADR-003`,
unrelated — yet all of it lives in `rag/retriever/hybrid.py` (`vector_weight=0.7`,
`keyword_weight=0.3` at line 14; the normalize-and-blend at lines 70–93;
`min_score=0.3` cutoff at line 93). The doc describes hybrid retrieval in a single
sentence and never explains how the two scores combine.

Reproduction evidence:

```text
$ grep -ci "blended|vector_weight|keyword_weight|normal|min_score|formula" docs/ARCHITECTURE.md
0    # none of the scoring concepts appear in the doc

$ grep -n "vector_weight\|keyword_weight\|blended_score\|min_score" rag/retriever/hybrid.py
14:  vector_weight: float = 0.7, keyword_weight: float = 0.3
78:  blended_score = (self.vector_weight * vector_score + self.keyword_weight * keyword_score)
93:  results = [r for r in blended.values() if r["score"] >= min_score]
```

**PLAN.md link:** https://github.com/yic04/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
The issue text says the scores are "min-max normalized," but the code actually
divides each score by the max of its own result set (max-normalization, no `min`
subtracted). My plan is to document the code's real behavior; I'll confirm with
the maintainer whether the code or the issue wording is the intended one before
Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix. I re-read `rag/retriever/hybrid.py`, `vector_store.py`, and
`keyword_search.py` to confirm the exact behavior, then added a new
"Hybrid Retrieval Scoring" subsection under RAG System in `docs/ARCHITECTURE.md`.
It documents the two-retriever pipeline (each fetches `max_chunks * 2`
candidates), the max-normalization step, the blending formula
(`blended = vector_weight * vector_norm + keyword_weight * keyword_norm`) with
defaults 0.7 / 0.3, the `min_score = 0.3` cutoff, and a worked example. This
completes sub-tasks 1–5 from PLAN.md.

I also resolved the Week 8 open question: rather than reproduce the issue's
"min-max normalized" wording, I documented what the code actually does
(max-normalization — divide by max, no min subtracted) and explicitly flagged
the distinction in the doc, since that is the behavior a reader will observe.

**Next steps:**
Finalize the wording, run `make check` / `make test-unit` to record the baseline
vs. post-change state, then open the PR against upstream and fill in the template.

**Blockers:**
None on the fix itself. Note: the local `.venv` is broken (no `pip`, no
`_pytest`, no `pre_commit`), so `make test-unit` and the pre-commit hook can't
run locally — this is a pre-existing environment issue, unrelated to a
docs-only change. Documented in Check-in 2.

---

### Check-in 2 (end of week)

**PR link:** _(fill in after opening the PR — https://github.com/ascherj/pathreview/pull/XXX)_

**Branch:** `docs/36-hybrid-retrieval-scoring-formula`

**What you built:**
A new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md` that
explains how `HybridRetriever` blends vector-similarity and BM25 keyword scores
into a single ranked list: the candidate-fetch pipeline, the max-normalization
of each retriever's scores to 0–1, the weighted blending formula with default
weights (0.7 / 0.3), the `min_score = 0.3` cutoff, and a worked example with
concrete numbers. No application code changes — the behavior was already
implemented; only the documentation gap is closed.

**Tests added or updated:**
None. This is a documentation-only change to a Markdown file; there is no
runtime behavior to test. `ruff` and `pytest` do not cover `.md` files
(confirmed: `ruff check docs/ARCHITECTURE.md` reports "No Python files found").
The worked-example numbers were hand-verified against the formulas in
`rag/retriever/hybrid.py`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

_"Passes" here means my change introduces no new failures, per the pre-existing-failure
guidance. Baseline (before my change): `make check` fails with 182 pre-existing `ruff`
errors in existing Python/test files; `make test-unit` cannot run because the local
`.venv` is broken (`ModuleNotFoundError: No module named '_pytest'`, and `pip` is
absent). My change touches only `docs/ARCHITECTURE.md`, which is outside the scope of
`ruff`/`mypy`/`pytest`, so it introduces zero new failures in either command._

**Draft PR feedback received from:** none
