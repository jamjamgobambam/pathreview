## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a has_tests boolean to the repo analysis output #50

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The repository-analysis pipeline does not currently indicate whether a project contains automated tests, leaving out a useful signal when evaluating a developer’s work. The GitHub inspection and analysis code in agent/tools/github_tool.py and agent/tools/repo_analyzer.py needs to recognize common test indicators, including test/ or tests/ directories, pytest.ini, and Python files named test_*.py. A successful fix would expose the result consistently as a has_tests boolean in the repository analysis output.


**Branch name:** feat/50-has-tests-detection

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/TheDarkFyre/pathreview/commit/6ec80998fa0cae23df58d05f08fc81d6de845e99

**Reproduction summary:**
Wrote a mocked unit test (`tests/unit/test_github_tool.py`) that calls `GitHubTool.execute()` for a repo known to have real tests and asserts `has_tests` is in the returned metadata — it fails, since `agent/tools/github_tool.py` never computes or includes that field at all. I also confirmed `ingestion/parsers/repo_analyzer.py` has separate `has_tests` detection logic, but it's dead code: it depends on a `file_structure` key nothing ever populates, and its only caller has zero call sites anywhere in the app.

**PLAN.md link:** https://github.com/TheDarkFyre/pathreview/blob/feat/50-has-tests-detection/PLAN.md

**Blockers or open questions:**
Still need to confirm whether `GitHubTool` is ever constructed with an `api_token` in practice — my planned fix adds one more GitHub API call per repo (root contents listing) to detect tests, and unauthenticated requests are already rate-limited to 60/hr, so I want to check real usage before finalizing in Week 9. Also scoped the fix to root-level test indicators only (won't catch nested test dirs like `backend/tests/`) — noted as a known limitation in PLAN.md rather than something to solve now.
