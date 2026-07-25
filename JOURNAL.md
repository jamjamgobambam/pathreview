## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/40

**Issue title:** Implement an offline eval runner that measures review quality across a benchmark portfolio set

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now, PathReview's eval suite only runs inline as part of live API requests, which means there's no way to check review quality across a broad set of portfolios without triggering real requests each time. This issue asks for a standalone script (`scripts/run_evals.py`) that runs the full RAG pipeline offline against a curated benchmark set of portfolios and writes out a JSON report of quality scores. The work touches the RAG evaluation logic in `rag/evaluator/eval_suite.py`, which will likely need to be refactored or reused so it can run outside the API request path. A successful fix gives the team a repeatable, on-demand way to measure review quality without needing to hit the live API.

**Branch name:** feat/40-offline-eval-runner

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (added after commit — see below)

**Reproduction summary:**
Ran scripts/run_evals.py and confirmed it is a stub. It prints success messages but never creates eval_results.json. Also found that EvalSuite, RelevanceScorer, and FaithfulnessChecker are not called anywhere in api/, only in their own tests.

**PLAN.md link:** https://github.com/SumaiaAlhemyari/pathreview/blob/feat/40-offline-eval-runner/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
No mock version of the review generator exists yet, and there are no sample benchmark portfolios yet. Both need to be created before the real eval runner can work end to end.
