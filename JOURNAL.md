# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` currently states that hybrid retrieval blends vector
similarity and keyword scores, but it never shows the actual formula or the
default weighting between the two signals. A reader can't tell how much a
document's semantic match versus its keyword match contributes to its final
rank, or how to tune that balance. This affects the RAG/retrieval
documentation rather than the retrieval code itself. A successful fix adds a
clear section to `docs/ARCHITECTURE.md` that spells out the scoring formula,
states the default weights, and walks through a worked example so future
contributors can reason about (and safely adjust) retrieval ranking.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this issue right for me?" checklist

**Part 1 — Understanding the issue.** In my own words: the architecture doc
says retrieval is "hybrid" (vector + BM25 keyword) but never says *how* the
two scores are combined, so a reader can't predict or tune ranking. The
affected area is the RAG docs (labels: `docs`, `rag`), and the one referenced
file — `docs/ARCHITECTURE.md` — exists; its RAG section currently gives the
blend exactly one sentence. "Done" looks like: before, the doc mentions
blending with no formula; after, it has a section stating the formula
(`score = 0.7 * normalized_vector + 0.3 * normalized_keyword`, per
`HybridRetriever` in `rag/retriever/hybrid.py`), the default weights, the
max-normalization step, and a worked example with sample numbers.

**Part 2 — Tier fit.** Tier 1 is right for me: this is my first contribution
to this codebase, and the change is a self-contained documentation update to
a single file. It fits the "documentation update" scope in the tier table.

**Part 3 — Codebase readiness.** I read `rag/retriever/hybrid.py`
end-to-end, not just located it: `HybridRetriever.__init__` sets
`vector_weight=0.7` / `keyword_weight=0.3`, and `retrieve()` normalizes each
score set by its max, blends per chunk, filters by `min_score=0.3`, and
returns the top `max_chunks=10`. That's everything the doc section needs, so
I can draft the fix without further lookups. On tests: there is no
`test_hybrid.py` today (only `test_keyword_search.py` covers the retriever
package), but since this issue changes only documentation, no new test is
required — the "read the test file" item doesn't gate a docs fix.

**Part 4 — Scope and time.** Estimated effort on the issue is 2–3 hours,
which fits comfortably in the Weeks 8–9 window: read the code (done), write
the doc section with a worked example, and verify the numbers against the
implementation. The issue lists no "blocked by" dependencies and stands
alone. Remaining to-do: check the Claims column in the cohort ledger and
comment on the issue to record my claim.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/knowbibek/pathreview/commit/8562401290b8b29cc5220a28af0f6bc6a342f0bd

**Reproduction summary:**
Because this is a documentation-gap issue rather than a runtime bug, I
reproduced it by tracing the retrieval code and confirming the doc omission.
The blend is implemented in `rag/retriever/hybrid.py` — defaults
`vector_weight=0.7` / `keyword_weight=0.3` in the constructor
([hybrid.py:13-14](rag/retriever/hybrid.py#L13-L14)) and the max-normalized
weighted sum in `retrieve()`
([hybrid.py:57-90](rag/retriever/hybrid.py#L57-L90)) — yet
`docs/ARCHITECTURE.md` mentions the blend in exactly one sentence
([ARCHITECTURE.md:60](docs/ARCHITECTURE.md#L60)) with no formula, weights, or
example. I also confirmed `HybridRetriever` is never instantiated elsewhere,
so the constructor defaults are the only source of the weights. The gap is
real and localized to that one doc file.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** https://youtu.be/UjrDfip7_w4

**Blockers or open questions:**
None blocking. Open question for Week 9: how much of the post-blend behavior
(`min_score` threshold, `max_chunks` cutoff, BM25 tokenizer) to document
versus keeping the section focused strictly on the formula + weights + example
the issue asks for. Current plan leans toward mentioning the thresholds
briefly and no further.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: added a new "Hybrid Retrieval Scoring"
subsection to `docs/ARCHITECTURE.md`, right after the existing RAG System
paragraph. It covers the blending formula, the default weights
(`vector_weight=0.7`, `keyword_weight=0.3`), the max-normalization step
applied to each score set before blending, a worked two-chunk numeric
example showing how normalization and weighting affect the final ranking,
and a short note on the post-blend `min_score`/`max_chunks` filtering. This
completes PLAN.md steps 2–4. Before starting, I captured a baseline of
`make check`/`make test-unit` on `main`: 182 pre-existing lint errors, 5
pre-existing mypy errors (all missing type stubs), and 53 failed / 375
passed unit tests — none in `docs/` or touching `rag/retriever/hybrid.py`,
so they're unrelated to this issue.

**Next steps:**
Finish PLAN.md step 5 — proofread the new section against
`rag/retriever/hybrid.py` line-by-line to confirm every number and file
reference is accurate. Re-run `make lint`/`make typecheck` after the edit to
confirm the pre-existing counts are unchanged. Then push the branch, open
the PR against the upstream repo as a draft, and request peer review in
Slack before marking it ready.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/399

**Branch:** docs/36-hybrid-retrieval-scoring-formula

**What you built:**
Added a "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md`
explaining how `HybridRetriever` blends vector and BM25 keyword scores: the
formula, the default weights (`vector_weight=0.7`, `keyword_weight=0.3`),
the max-normalization step applied before blending, and a worked two-chunk
example showing how the ranking comes out. Documentation-only change — no
code behavior was modified.

**Tests added or updated:**
None — this is a documentation-only fix with no code behavior change, so no
new tests apply. Baselined `make lint`/`make typecheck`/`make test-unit`
before and after the edit: 182 pre-existing lint errors, 5 pre-existing
mypy errors (missing type stubs), and 53 pre-existing failing unit tests,
all identical before and after — none touch `docs/` or
`rag/retriever/hybrid.py`, so this change introduces no new failures.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(both confirmed against the pre-existing baseline — no new failures introduced by this change; see Testing section of the PR description for counts)*

**Draft PR feedback received from:** none — I opened the PR as a draft
earlier in the week but forgot to actually post it in the cohort Slack
channel for review until Sunday, close to the deadline, so no feedback came
in before submitting. Marked ready for review to submit on time; open to
addressing any feedback that comes in after the fact.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No comments or reviews came in on PR #399 by the end of the module. (Per
the Su26 course note, reviewer feedback isn't a live feature this term, so
this was expected.)

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
The whole four-week cycle was demanding but genuinely engaging. Since #36
turned out to be a documentation-only issue, in hindsight I think a
code-level bug would have pushed me harder — tracing `hybrid.py` to get the
formula right was useful, but I didn't have to touch the actual codebase
logic or write new tests, so I came away wondering if I picked the "safe"
issue instead of the one that would've taught me the most.

**What did you learn about working in a large codebase?**
Mostly about collaboration and structure — how a real project is
organized, how the pieces fit together (API layer → ingestion → agent →
RAG → safety), and what the contribution workflow looks like end to end,
from picking an issue through opening a PR. Seeing that high-level shape
was something I genuinely enjoyed.

**How did AI tools help — and where did they fall short?**
I used Claude and Gemini throughout — genuinely useful for automating parts
of the process and drafting code and docs, but not infallible: sometimes
what looked correct was actually a hallucination, so I had to verify things
myself rather than trust the output blindly. If you don't already
understand the syntax or the problem, the tool can give you a false sense
of confidence. The real lesson: the tool isn't what produces a good result
— the person driving it, verifying its output, and asking it the right
questions is.

**What would you do differently if you started over?**
Stay ahead of deadlines instead of scrambling — I forgot to actually post
my PR in the Slack review channel until Sunday, right before the deadline,
which left no time for real feedback. I'd also lean on the cohort community
more throughout the month, asking questions there while working on my own
side projects in parallel, instead of only engaging reactively at crunch
time.

**What are you most proud of from this module?**
Finishing the course built real discipline for me. I wasn't consistently
working on things before this, but going through this structured
four-week cycle gave me momentum and a habit of staying focused on the
work. While going through it — and doing research alongside the
coursework — I ended up finding something that mattered to me beyond just
this class. Getting back into that rhythm and rediscovering that momentum
is what I'm most proud of, more than the PR itself.
