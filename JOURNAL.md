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
