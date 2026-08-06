## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Detection logic needs to be added to check for the presence of test coverage in a repository. This issue asks for a has_tests boolean to be added as the detection logic. A successful fix would accomplish an automatic confirmation of test coverage in a repository. Relevant files are agent/tools/github_tool.py and ingestion/parsers/repo_analyzer.py, which the latter is incorrectly stated in the issues description.

**Branch name:** test/50-add-has-test-boolean

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/amyng939/pathreview/commit/95a528c6a51c423645ddd654d1db4f52ccdcdcb8#diff-46b5a285f91f98e0792efcd3027382c5e08bdd89ace225610da6e03f353be190

**Reproduction summary:**
Ran in the project venv: `python -c "from agent.tools.github_tool import GitHubTool; d = GitHubTool().execute({'github_username':'octocat','repo_name':'Hello-World'}).data; print(sorted(d)); print('has_tests present?', 'has_tests' in d)"`; the returned keys were ['description', 'fork_count', 'has_readme', 'homepage', 'last_commit_date', 'name', 'open_issues_count', 'primary_language', 'star_count', 'topics'] — confirming no has_tests key exists. The gap is in _fetch_repo_metadata() at agent/tools/github_tool.py:100, which builds the metadata dict but has no has_tests entry and the class has no _detect_tests() method (only _has_readme()).

**PLAN.md link:** https://github.com/amyng939/pathreview/blob/test/50-add-has-test-boolean/PLAN.md

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
So far I started implementing the first sub-task from PLAN.md which is adding a _detect_tests() method to githubtool.

**Next steps:**
Finishing up the _detect_tests() method, adding has_tests to the metadata dict, and adding a unit test to ensure correct behavior.

**Blockers:**


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1000

**Branch:** test/50-add-has-test-boolean

**What you built:**
Added a `has_tests` boolean to `GitHubTool`'s output. A new `_detect_tests()` method fetches the repository's recursive git tree (`GET /repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1`) and returns `True` if any path is a `tests/`/`test/` directory, a `pytest.ini`, or a `test_*.py` file — matching whole path segments (so `contest/`/`latest/` don't false-positive) and case-insensitively, failing safe to `False` on any error. `_fetch_repo_metadata()` now reads `default_branch` from the API response (falling back to `"main"`) and includes `"has_tests"` in the returned metadata dict, next to `has_readme`.

**Tests added or updated:**
Wrote `tests/unit/test_github_tool.py` into a mocked, network-free unit suite of 13 cases across two classes. `TestDetectTests` covers detection via a `tests/`/`test/` dir, `pytest.ini`, and root-level `test_*.py`; case-insensitivity; the `contest/`/`latest/` false-positive guard; empty repo; fail-safe on request error; and the API-token auth header. `TestFetchRepoMetadata` covers the end-to-end `execute()` output (asserting `has_tests` plus no regression on existing fields) and the `default_branch` fallback to `main`.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
Ensuring that no changes have been made to previous passes after adding new code

**Draft PR feedback received from:** none
