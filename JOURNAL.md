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


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five sub-tasks from PLAN.md are done. Added sample benchmark portfolios in tests/fixtures/sample_profiles/. Added a mock review generator in rag/generator/mock_generator.py so the script runs without a real API key. Rewrote scripts/run_evals.py to actually run retrieval, generation, and evaluation, and write eval_results.json. Added tests/unit/test_mock_generator.py and tests/unit/test_run_evals.py.

**Next steps:**
Open the pull request and get feedback on it before marking it ready for review.

**Blockers:**
Found that VectorStore.add_chunks was dead code with a broken interface. Worked around it instead of fixing it, since fixing it is outside the scope of this issue.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/554

**Branch:** feat/40-offline-eval-runner

**What you built:**
A real offline eval runner that loads sample portfolios, runs them through search and review generation, scores the results, and writes real scores to eval_results.json. Before this, the script only printed messages and never actually ran anything.

**Tests added or updated:**
Added tests/unit/test_mock_generator.py, which covers the mock review generator returning correct fields, staying consistent for the same input, and working without any real API calls. Added tests/unit/test_run_evals.py, which covers loading the sample portfolios, running one portfolio through the full pipeline, handling a portfolio with no chunks without crashing, and running the whole script end to end to confirm it writes a valid report.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass in the sense that no new failures were introduced. The codebase already had 182 lint errors and 53 failing tests before this change, confirmed by checking before starting. My new files are lint-clean, and all new tests pass.)

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review comments came in on the pull request before the course ended.

**How you responded:**
Not applicable, since no feedback arrived.

---

### Reflection

**What was harder than you expected?**
Getting a working local environment was harder than the actual coding. I hit a real bug in a pinned Docker image, where ChromaDB and numpy were incompatible with each other. I also tried running Docker inside a Docker container, which does not work because of how overlay filesystems stack. I had to switch to a real virtual machine before I could even start on the issue itself.

**What did you learn about working in a large codebase?**
The issue description did not fully match the real code. It said the eval logic ran during live requests, but when I checked, that code was never called anywhere except its own tests. I also found a second bug on my own: a class that was never used anywhere and had a broken interface. Working in someone else's codebase means checking what the code actually does, not just trusting what the issue says.

**How did AI tools help — and where did they fall short?**
AI was useful for reading through unfamiliar files quickly and for writing repetitive test code. It fell short on judgment calls, like deciding what counted as in scope for the issue, and on tooling problems that needed real trial and error, like the Docker setup and a mypy version mismatch. Those needed actual investigation, not just a generated answer.

**What would you do differently if you started over?**
I would confirm the local environment setup actually works end to end before assuming a plan will work, instead of discovering problems partway through setup. I would also read the actual code the issue points to before trusting the issue's own description of the problem.

**What are you most proud of from this module?**
Finding that the eval code the issue described as already running live was actually never connected to anything. That was not something the issue told me. I found it myself by checking the real code.
