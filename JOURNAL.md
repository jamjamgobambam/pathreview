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

**PR link:** https://github.com/ascherj/pathreview/pull/733 (currently draft — will update once marked ready for review)

**Branch:** docs/36-hybrid-retrieval-scoring-formula

**What you built:**
Added a "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md` that documents the exact scoring formula `HybridRetriever` uses to blend vector and BM25 search results (per-result-set min-max normalization, weighted sum with 0.7/0.3 defaults, min-score filtering), plus a worked numeric example. Docs-only change — no application code modified.

**Tests added or updated:**
None — this is a documentation-only fix with no code path changes, so no test files were touched.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
(Both commands were run before and after this change; the same 53 pre-existing test failures and 182 pre-existing lint errors appear in both runs, none in `docs/ARCHITECTURE.md` — confirming no new failures were introduced. Checkboxes left unchecked here since the pre-existing failures mean the commands don't pass outright; see PR description for the documented baseline.)

**Draft PR feedback received from:** none yet.
