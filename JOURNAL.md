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
https://github.com/fyf820/pathreview/commit/1ba8a122077083ccd100333fbb23b00819667ff1
 
**Reproduction summary:**
- `agent/tools/github_tool.py` already fetches repo metadata via the GitHub API and includes a `_has_readme()` helper — the same shape I'd follow for `_has_tests()`. No test-detection logic exists there yet.
- `agent/tools/repo_analyzer.py` doesn't exist yet, despite the issue referencing it as if it does. I'll either create it or add the detection logic alongside `tech_detector.py`, which already does similar file-pattern detection — need to check that file before deciding where this belongs.
- `tests/unit/` has 20 test files, but none for `github_tool` or a repo analyzer, confirming this is a green-field addition with no prior coverage to build on.

**PLAN.md link:** [link to PLAN.md](PLAN.md)

**Walkthrough video (recommended):** 
[video](https://drive.google.com/file/d/1R4i9djhqMbMb0Xcr4T3YLzRhPwFEphc6/view?usp=sharing)

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all three sub-tasks from PLAN.md: added `_fetch_file_tree()` to `agent/tools/github_tool.py` so repo metadata includes the file paths from the default branch, created `agent/tools/repo_analyzer.py` with the `has_tests` detection logic (checks for `tests/`/`test/` directories, `pytest.ini`, and `test_*.py` files), and wired `repo_analyzer` into `Orchestrator._build_plan()` alongside `tech_detector` whenever file data is present.

**Next steps:**
Push the branch, open the PR against `ascherj/pathreview`, and get draft feedback.

**Blockers:**
The mypy pre-commit hook failed on pre-existing missing type annotations in `agent/error_handling.py`, `agent/memory/context_manager.py`, and `agent/memory/session_store.py` — files I never touched, but which get type-checked transitively because `orchestrator.py` imports them. Fixed those annotations in their own `chore` commit, separate from the feature commit, so the diff stays easy to review.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/818

**Branch:** [feat/50-detect-has-tests](https://github.com/fyf820/pathreview/tree/feat/50-detect-has-tests)


**What you built:**
Added a new `RepoAnalyzer` tool (`agent/tools/repo_analyzer.py`) that checks a repo's file paths for a `tests/`/`test/` directory, a `pytest.ini`, or `test_*.py` files, and returns that as a `has_tests` boolean. Extended `github_tool.py` to fetch the repo's file tree so there's data to check against, and wired `repo_analyzer` into the orchestrator's plan alongside `tech_detector` whenever file data is available.

**Tests added or updated:**
- `tests/unit/test_repo_analyzer.py` — parametrized cases for detecting common test-path signals, not false-positiving on unrelated files, and defaulting to `False` when the `files` key is missing.
- `tests/unit/test_github_tool.py` — file tree fetch is included in repo metadata, and gracefully degrades to an empty list on failure.
- `tests/unit/test_orchestrator.py` — plan includes `repo_analyzer` when files are present and skips it otherwise.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
Scoped to the files this PR touches: `ruff`/`black`/`mypy` (via pre-commit) pass on every changed file, and the new/updated tests (`test_repo_analyzer.py`, `test_github_tool.py`, `test_orchestrator.py`, 15 tests total) pass. Repo-wide, `make check`/`make test-unit` do not pass — `ruff check .` has 174 pre-existing errors and the full unit suite has 53 pre-existing failures, both in modules unrelated to and untouched by this change (`test_review_service.py`, `test_security.py`, `test_skill_extractor.py`, etc.).

**Draft PR feedback received from:** none