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

**PR link:** https://github.com/ascherj/pathreview/pull/807

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
Added `tests/unit/test_hybrid.py` — a new `TestHybridRetrieverScoring` suite
(6 tests) covering the scoring behavior I documented, using stubbed
vector/keyword backends so only the blend logic is exercised:
- `test_worked_example_matches_documentation` — asserts the exact worked example
  from the doc (A=0.700, B=0.765, C=0.300) and the resulting B > A > C ranking.
- `test_single_retriever_chunk_gets_zero_for_missing_signal` — a chunk found by
  only one retriever contributes 0 for the missing signal (vector-only → 0.7,
  keyword-only → 0.3).
- `test_min_score_cutoff_drops_low_scoring_chunks` — chunks below `min_score`
  are filtered out before ranking.
- `test_max_chunks_truncates_to_top_scoring` — at most `max_chunks` results,
  highest scores first.
- `test_empty_results_returns_empty_list` — no candidates → empty list (no
  divide-by-zero on the `max` normalization).
- `test_custom_weights_change_the_blend` — non-default `vector_weight` /
  `keyword_weight` are applied to the normalized scores.

The expected numbers were independently verified against a standalone
reimplementation of the blend from `rag/retriever/hybrid.py`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

_"Passes" here means my change introduces no new failures, per the pre-existing-failure
guidance. I rebuilt the `.venv` (a system Python upgrade 3.12 → 3.14 had broken the
old one) and ran the full suite on both branches:_

- _`make test-unit` on `main`: **53 failed, 375 passed** (pre-existing failures across
  ~10 unrelated files — `test_pii_scrubber`, `test_resume_parser`,
  `test_review_service`, `test_skill_extractor`, etc.)._
- _`make test-unit` on this branch: **53 failed, 381 passed** — the same 53
  pre-existing failures, plus my 6 new `test_hybrid.py` tests all passing. **Zero new
  failures introduced.**_
- _`tests/unit/test_hybrid.py` passes `ruff` and `black --check`; `mypy` in `make check`
  scopes to `api/ core/ ingestion/ rag/ agent/ safety/`, not `tests/`, so the test file
  is out of its scope. `make check` still reports its pre-existing `ruff`/`mypy` errors
  in existing files, none of them from my changes._

**Draft PR feedback received from:** Shanhe

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer review has landed on the upstream PR (#807) yet. The only feedback
so far came earlier in the cycle: Shanhe reviewed the draft PR and confirmed the
scoring explanation read clearly and matched the code — no substantive changes
requested.

**How you responded:**
Nothing to respond to from a maintainer yet. From Shanhe's draft pass I tightened
a couple of phrasings but made no structural changes. If a maintainer requests
changes after this entry, I'll follow up on the PR thread; the most likely point
of discussion is the "min-max vs. max-normalization" wording I flagged in the doc
(see Week 8), so I've kept that section deliberately explicit to pre-empt it.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't writing the documentation — it was trusting my own reading
of the code over the issue text. The issue confidently said the scores are
"min-max normalized," but when I actually traced `rag/retriever/hybrid.py`, the
code divides each score by the max of its own result set with no `min` subtracted
— that's max-normalization, a different operation. Deciding to document what the
code *does* rather than what the issue *says*, and flagging the discrepancy
explicitly, felt uncomfortable for a first contribution. A close second was the
environment: a system Python upgrade (3.12 → 3.14) had quietly broken my `.venv`,
so `make test-unit` and the pre-commit hook wouldn't run at all. Rebuilding the
venv and then untangling *my* results from the 53 pre-existing test failures on
`main` took longer than writing the actual change.

**What did you learn about working in a large codebase?**
That "a docs-only change" is never really docs-only — to write one honest
paragraph about the scoring formula I had to read three files (`hybrid.py`,
`vector_store.py`, `keyword_search.py`) and hold the whole retrieval pipeline in
my head. Contributing to someone else's production code is mostly comprehension,
not typing. The other big difference from my own projects: I don't get to define
what "passing" means. The suite already had 53 failures I didn't cause, so I had
to establish a baseline on `main`, re-run on my branch, and prove I added *zero
new failures* rather than assuming a green run. In my own repo I'd have just
fixed everything until it was green; here, respecting the existing state of the
codebase — and the pre-existing-failure guidance — was the correct move.

**How did AI tools help — and where did they fall short?**
AI was most useful as an accelerant for navigation and verification: quickly
locating the weight defaults and the normalize-and-blend block, drafting the
stubbed vector/keyword backends for the test suite, and sanity-checking the
worked-example arithmetic (A=0.700, B=0.765, C=0.300). Where it fell short was
exactly the part that mattered most — noticing that the issue's "min-max"
description didn't match the code. That required deliberately reading the actual
normalization line and *disbelieving* the confident prose around it, which is a
judgment call, not a lookup. AI happily echoes whatever framing you feed it; the
independent verification of the blend numbers against a hand-written
reimplementation, and the decision to document real behavior over stated
behavior, were mine.

**What would you do differently if you started over?**
I'd verify my toolchain in Week 7 instead of discovering the broken `.venv` at
PR time in Week 9 — a five-minute `make test-unit` up front would have saved a
scramble later. I'd also raise the min-max vs. max-normalization discrepancy with
the maintainer the moment I found it in Week 8, as a comment on the issue, rather
than carrying it as an open question into the implementation week. Getting that
answer early would have let me write the doc with full confidence rather than
hedging. On issue selection I have no regrets — a well-scoped Tier 1 docs issue
was the right foothold for a first contribution to this codebase.

**What are you most proud of from this module?**
That I didn't treat "just a docs issue" as a license to be shallow. I added a
6-test unit suite for behavior nobody asked me to test, verified the numbers
independently, and caught a real inaccuracy in the issue's own description of the
code. The deliverable was a paragraph of documentation, but the work behind it
was genuine engineering — reading the system carefully enough to explain it
truthfully, and being willing to say "the code actually does something else."
