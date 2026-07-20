## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a has_tests boolean to the repo analysis output #50

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The repository-analysis pipeline does not currently indicate whether a project contains automated tests, leaving out a useful signal when evaluating a developer’s work. The GitHub inspection and analysis code in agent/tools/github_tool.py and agent/tools/repo_analyzer.py needs to recognize common test indicators, including test/ or tests/ directories, pytest.ini, and Python files named test_*.py. A successful fix would expose the result consistently as a has_tests boolean in the repository analysis output.


**Branch name:** feat/50-has-tests-detection

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
