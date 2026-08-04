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

## Week 9 — Implementation

**Implementation commit link:** https://github.com/shanhe2/pathreview/commit/fdf8c1a

**Open-question follow-up:** Grepped the repo for `.index(` calls on `KeywordSearcher` — the only call site is in `tests/unit/test_keyword_search.py`; nothing in the ingestion or retrieval code path builds the BM25 index before `HybridRetriever.retrieve()` calls `keyword_searcher.search()`. Confirms this is a real, separate bug (the keyword-search branch appears unreachable in practice) but it's out of scope for issue #36's doc-only fix, so the new section describes the scoring formula as designed without asserting the BM25 half is currently wired up end-to-end.

**What changed:** Replaced the issue #36 reproduction comment in `docs/ARCHITECTURE.md` with a full "Hybrid Retrieval Scoring" subsection: the two normalized inputs, the min-max-per-result-set caveat, the weighted-sum formula, default weights (`vector_weight=0.7`, `keyword_weight=0.3`) with a one-line rationale, the `min_score` filter step, a note on missing-side chunks scoring 0, and the worked A/B example from `PLAN.md` as a table. No code changes — matches the issue's docs-only scope.

**Testing:** No unit tests apply (docs-only change). Ran `make test-unit` and `make check` before and after; both show the same 53 pre-existing test failures and 182 pre-existing lint errors, none in files this change touches (`docs/ARCHITECTURE.md` is the only file modified) — confirming this change introduces no new failures.

**Self-review:** Re-read `rag/retriever/hybrid.py` line by line against the new doc section to confirm the formula, defaults, and normalization order match exactly; proofread the worked example arithmetic.
