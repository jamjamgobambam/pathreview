# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` mentions that the RAG pipeline's hybrid retrieval step blends vector similarity search with BM25 keyword search, but it never spells out how those two scores are actually combined into one ranking. There's no formula, no default weighting between the vector and keyword components, and no worked example showing how a candidate document's final score is derived. This makes the retrieval stage hard to reason about or tune for anyone reading the doc without going straight to the source. A successful fix adds a section to `docs/ARCHITECTURE.md` that states the scoring formula explicitly, gives the default weights, and walks through a concrete example calculation, so the hybrid retrieval behavior is understandable from the docs alone. This only touches documentation — no code in the retrieval path changes.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**"Is this right for me?" checklist reasoning:**
- **Scope is bounded:** the fix is confined to a documentation file (`docs/ARCHITECTURE.md`); no application code, migrations, or tests are affected, so there's low risk of breaking anything while my local environment setup is still in progress.
- **Matches tier:** it's labeled Tier 1, and the actual work (reading the retrieval scoring code, writing a clear explanation and example) matches a Tier 1-sized task — no new abstractions or architectural decisions required. This also matches my own comfort level: I'm solid with Python generally, but this is my first time in the pathreview codebase, so a docs-only issue lets me read through the real retrieval implementation and get oriented before taking on a Tier 2/3 issue that changes application code.
- **Requires reading real code:** even though the deliverable is docs-only, I need to actually find and read the hybrid scoring implementation (likely in `rag/`) to describe the true formula and defaults accurately rather than guessing, which is a reasonable amount of investigation for a first issue.
- **No blocking dependencies:** the issue doesn't depend on other in-flight issues or infra changes, so I can pick it up immediately once my environment is set up.
