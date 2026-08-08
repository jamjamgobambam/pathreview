# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` mentions that the RAG pipeline's hybrid retrieval step blends vector similarity search with BM25 keyword search, but it never spells out how those two scores are actually combined into one ranking. There's no formula, no default weighting between the vector and keyword components, and no worked example showing how a candidate document's final score is derived. This makes the retrieval stage hard to reason about or tune for anyone reading the doc without going straight to the source. A successful fix adds a section to `docs/ARCHITECTURE.md` that states the scoring formula explicitly, gives the default weights, and walks through a concrete example calculation, so the hybrid retrieval behavior is understandable from the docs alone. This only touches documentation — no code in the retrieval path changes.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" checklist reasoning:**
- **Scope is bounded:** the fix is confined to a documentation file (`docs/ARCHITECTURE.md`); no application code, migrations, or tests are affected, so there's low risk of breaking anything while my local environment setup is still in progress.
- **Matches tier:** it's labeled Tier 1, and the actual work (reading the retrieval scoring code, writing a clear explanation and example) matches a Tier 1-sized task — no new abstractions or architectural decisions required. This also matches my own comfort level: I'm solid with Python generally, but this is my first time in the pathreview codebase, so a docs-only issue lets me read through the real retrieval implementation and get oriented before taking on a Tier 2/3 issue that changes application code.
- **Requires reading real code:** even though the deliverable is docs-only, I need to actually find and read the hybrid scoring implementation (likely in `rag/`) to describe the true formula and defaults accurately rather than guessing, which is a reasonable amount of investigation for a first issue.
- **No blocking dependencies:** the issue doesn't depend on other in-flight issues or infra changes, so I can pick it up immediately once my environment is set up.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shanhe2/pathreview/commit/6f1d51e

**Reproduction summary:**
Read `docs/ARCHITECTURE.md`'s RAG System section end to end and confirmed it never states how vector and BM25 scores combine. Traced the actual blending logic to `rag/retriever/hybrid.py:57-81`, which min-max normalizes each score within its result set and combines them via `score = vector_weight * vector_norm + keyword_weight * keyword_norm` (defaults 0.7/0.3, `hybrid.py:14`) — none of which appears in the doc. Documented this gap with a note in `docs/ARCHITECTURE.md` pointing to the exact code lines.

**PLAN.md link:** https://github.com/shanhe2/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
`rag/retriever/hybrid.py` fetches all chunks for keyword search but I don't see where `KeywordSearcher.index()` actually gets called before `retrieve()` uses it — need to confirm where/whether the BM25 index is built (likely during ingestion) before finalizing the doc's description of the keyword-search step. This looks like a separate, unrelated bug and is out of scope for issue #36.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`: replaced the issue #36 reproduction comment in `docs/ARCHITECTURE.md` with a full "Hybrid Retrieval Scoring" subsection covering the two normalized inputs, the min-max-per-result-set caveat, the weighted-sum formula, default weights (`vector_weight=0.7`, `keyword_weight=0.3`) with a one-line rationale, the `min_score` filter step, a note on missing-side chunks scoring 0, and the worked A/B example from `PLAN.md` as a table (commit `fdf8c1a`). Re-read `rag/retriever/hybrid.py` line by line against the new section to confirm the formula, defaults, and normalization order match exactly. Also resolved the open question from Week 8: grepped for `.index(` calls on `KeywordSearcher` and found the only call site is in `tests/unit/test_keyword_search.py` — nothing in the real ingestion/retrieval path builds the BM25 index before `retrieve()` uses it. That's a real, separate bug, out of scope for this doc-only fix.

**Next steps:**
Open the PR against `main`, fill out the PR template, get a draft review from a classmate/mentor, address feedback, then mark it ready for review and submit by Sunday.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/733

**Branch:** docs/36-hybrid-retrieval-scoring-formula

**What you built:**
Added a "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md` that documents the exact scoring formula `HybridRetriever` uses to blend vector and BM25 search results (per-result-set min-max normalization, weighted sum with 0.7/0.3 defaults, min-score filtering), plus a worked numeric example. Docs-only change — no application code modified.

**Tests added or updated:**
None — this is a documentation-only fix with no code path changes, so no test files were touched.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both commands were run before and after this change; the same 53 pre-existing test failures and 182 pre-existing lint errors appear in both runs, none in `docs/ARCHITECTURE.md` — confirming this change introduces no new failures. See PR description for the documented baseline.)

**Draft PR feedback received from:** none.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments came in on PR #733 before this journal entry. The PR sat as a draft for peer/mentor review earlier in the week, but no one picked it up in time, so I marked it ready for review on my own judgment rather than holding the deadline hostage to feedback that might not arrive.

**How you responded:**
N/A — nothing to respond to yet. If feedback comes in after submission, I'll address it in follow-up commits on the same branch, since the PR stays open past the journal deadline.

---

### Reflection

**What was harder than you expected?**
Two things. First, scoping the fix correctly took more discipline than I expected for a "just write docs" issue. While tracing `HybridRetriever.retrieve()` I found that `KeywordSearcher.index()` is never called anywhere in the real ingestion/retrieval path — only in a unit test — which means the BM25 half of "hybrid" retrieval may be dead code in practice. That's a genuinely interesting, real bug, and I had to consciously stop myself from fixing it or even hedging the doc language around it, since issue #36 was scoped to documenting the formula as designed, not auditing whether it's wired up correctly. Flagging it in "Notes for Reviewers" instead of acting on it was the right call, but the pull to fix what I'd found was stronger than I expected.

Second, the process scaffolding was harder than the actual content. I got the technical explanation (the formula, the worked example, the normalization caveat) right on the first pass because I could verify it directly against the code. But I got the required journal format wrong on the first pass — I wrote an ad-hoc "Implementation" entry instead of the mandated Check-in 1 / Check-in 2 structure, which would have made the PR link undiscoverable to a grader looking for a specific heading. That was a "the code was right but the delivery wasn't" mistake, and it's the kind of error that's easy to make when you're focused on the interesting problem and treat the submission mechanics as an afterthought.

**What did you learn about working in a large codebase?**
The biggest shift was what "passing" means. `make test-unit` showed 53 failing tests and `make check` showed 182 lint errors before I ever touched anything — none related to my change. In a solo project, red test output means stop and fix it. Here, the correct response was to characterize the baseline (run it before and after, diff the failure set, confirm it's unchanged) and document that explicitly in the PR rather than either ignoring it or trying to fix unrelated code I don't understand well enough to safely touch. "My change introduces no new failures" is a different, more honest bar than "everything is green," and it's the one that actually applies to a shared codebase with pre-existing debt.

I also learned that documentation is a deliverable with its own correctness obligation, not a lesser task than code. Once `ARCHITECTURE.md` states a formula and default weights, readers will trust it without re-deriving it from `hybrid.py` themselves — so a wrong line number or a swapped default would actively mislead someone in a way that no doc at all wouldn't. That's why I re-read the implementation line-by-line against my own draft before opening the PR, treating it with the same scrutiny I'd want with a code review.

**How did AI tools help — and where did they fall short?**
AI assistance was strongest at mechanical consistency work: catching that my journal entry didn't match the required template, keeping the worked example's arithmetic and the prose description in sync as I edited, and drafting the PR body against the actual repo's `PULL_REQUEST_TEMPLATE.md` so nothing was left blank. It was also useful as a second pair of eyes cross-referencing the doc section against `hybrid.py` line numbers and defaults before I finalized anything.

It fell short anywhere the task required an action or a judgment call, not text generation. It couldn't open a PR because `gh` wasn't installed in the environment — I had to open it manually in the browser using a compare URL. It couldn't tell me whether reviewers had actually commented, whether the PR was truly marked ready, or supply the Week 9/10 journal templates from memory — those had to come from me, because guessing at a graded rubric format is worse than asking. The general pattern: AI was excellent at "is this consistent with what I already decided" and useless at "has this real-world thing happened yet."

**What would you do differently if you started over?**
I'd write the journal entries against the exact required template from Week 7 onward instead of drafting my own reasonable-looking format and needing a correction pass in Week 9. The content across weeks was fine, but reformatting after the fact is wasted motion that a five-minute check against the actual assignment instructions would have avoided. I'd also open the PR as a draft earlier in the week — I did it appropriately in sequence, but with more slack before the deadline, there would have been a real chance of getting feedback instead of ending the module with an unreviewed "ready for review" PR.

**What are you most proud of from this module?**
The line-by-line verification I did before finalizing the doc section — re-reading `rag/retriever/hybrid.py` against every claim in my `ARCHITECTURE.md` addition (the normalization order, the default weights, the min-score filter, the worked example's arithmetic) rather than trusting my Week 8 notes. It's not a visible or exciting part of the PR, but it's the difference between a documentation fix that's actually trustworthy and one that just looks plausible.
