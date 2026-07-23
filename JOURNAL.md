## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Detection logic needs to be added to check for the presence of test coverage in a repository. This issue asks for a has_tests boolean to be added as the detection logic. A successful fix would accomplish an automatic confirmation of test coverage in a repository. Relevant files are agent/tools/github_tool.py and ingestion/parsers/repo_analyzer.py, which the latter is incorrectly stated in the issues description.

**Branch name:** test/50-add-has-test-boolean

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger