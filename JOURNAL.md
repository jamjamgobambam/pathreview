## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/40

**Issue title:** Implement an offline eval runner that measures review quality across a benchmark portfolio set

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now, PathReview only checks review quality during a real request. There is no way to test many portfolios at once without making real requests each time. This issue asks for a new script, `scripts/run_evals.py`, that runs the full pipeline by itself, using a set of sample portfolios, and saves the scores to a JSON file. This work uses the code in `rag/evaluator/eval_suite.py`, which may need changes so it can run outside of a live request. Once finished, there will be an easy way to check review quality anytime, without needing to make real API calls.

**Branch name:** feat/40-offline-eval-runner

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SumaiaAlhemyari/pathreview/commit/a0507e9

**Reproduction summary:**
Ran scripts/run_evals.py and confirmed it is a stub. It prints success messages but never creates eval_results.json. Also found that EvalSuite, RelevanceScorer, and FaithfulnessChecker are not called anywhere in api/, only in their own tests.

**PLAN.md link:** https://github.com/SumaiaAlhemyari/pathreview/blob/feat/40-offline-eval-runner/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
No mock version of the review generator exists yet, and there are no sample benchmark portfolios yet. Both need to be created before the real eval runner can work end to end.
