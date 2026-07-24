## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a has_tests boolean to the repo analysis output #50

**Tier:** Tier 1

**Problem summary:**
When the agent reviews a candidate's GitHub repo, it currently has no way of telling whether the project has any automated tests at all, as repo with thorough test coverage and one with none look exactly the same to the scoring logic. Since having tests is one of the clearer signals of engineering maturity on a portfolio, this is a missing signal the review is currently blind to. The fix adds detection logic in new created `agent/tools/repo_analyzer.py`, using file-tree data already fetched by `agent/tools/github_tool.py`, that checks for a `tests/`/`test/` directory, a `pytest.ini`, or files matching `test_*.py`. A successful fix surfaces this as a new `has_tests` boolean on the analysis output, so later scoring and feedback can factor in whether a candidate's project is actually tested. 

**Problem fit:**
I've read the the file this issue touches (`agent/tools/github_tool.py`) and located the existing analyzer logic I'd be extending. I have some prior experience contributing to open source, but I'm still new to this specific codebase, so I chose a Tier 1 issue: it's a self-contained, additive check on top of an existing analyzer rather than a change to core matching or scoring logic. I also spent a significant amount of time getting my local environment and Docker working, hitting several failed setup attempts along the way, which made me want a lower-risk issue that wouldn't require touching a more complex or unfamiliar part of the stack in case my environment breaks again.

**Branch name:** feat/50-detect-has-tests

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 

 
**Reproduction summary:**
- `agent/tools/github_tool.py` already fetches repo metadata via the GitHub API and includes a `_has_readme()` helper — the same shape I'd follow for `_has_tests()`. No test-detection logic exists there yet.
- `agent/tools/repo_analyzer.py` doesn't exist yet, despite the issue referencing it as if it does. I'll either create it or add the detection logic alongside `tech_detector.py`, which already does similar file-pattern detection — need to check that file before deciding where this belongs.
- `tests/unit/` has 20 test files, but none for `github_tool` or a repo analyzer, confirming this is a green-field addition with no prior coverage to build on.

**PLAN.md link:** [link to PLAN.md](PLAN.md)

**Walkthrough video (recommended):** 

**Blockers or open questions:**