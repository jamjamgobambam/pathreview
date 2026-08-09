## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output — [#50](https://github.com/Alessandra005/pathreview/issues/50)

### Understand
The current repo metadata doesn’t indicate whether a project contains tests. This is an important quality signal we want to surface, similar to how we already report `has_readme`. Right now, the GitHubTool returns a metadata dictionary with fields like stars, forks, languages, and `has_readme`, but it never checks for test directories or test files. The fix is to extend the GitHubTool’s metadata generation so it detects common test patterns (e.g., `tests/`, `test/`, `test_*.py`) and adds a new boolean field `has_tests` to the output. Once implemented, any repo analyzed by the tool will clearly indicate whether it includes tests, improving the usefulness of the overall analysis.

### Expected Behavior
The metadata dict should include a new boolean field:
```python
has_tests: bool
```

### Map
- `agent/tools/github_tool.py` — `_fetch_repo_metadata` builds the `metadata` dict (name, description, star_count, has_readme, etc.); this is where a `has_tests` key needs to be added, and where a new `_has_tests` helper method (mirroring the existing `_has_readme`) should live.
- `tests/test_github_tool.py` (new file) — unit tests for the new `_has_tests` logic.

### Plan
1. Add a `_has_tests(self, username, repo_name)` method to `GitHubTool`, modeled on `_has_readme`: hit the GitHub contents API (`/repos/{owner}/{repo}/contents`) to list root-level files/folders, since there's no dedicated "has tests" endpoint like there is for READMEs.
2. In that method, check the returned names for: a `tests` or `test` directory, a `pytest.ini` file, or any file matching `test_*.py`.
3. Call `self._has_tests(username, repo_name)` inside `_fetch_repo_metadata` and add the result to the `metadata` dict as `"has_tests"`.
4. Write unit tests in `tests/test_github_tool.py` covering: repo with a `tests/` dir, repo with `pytest.ini`, repo with root-level `test_*.py` files, and a repo with none of the above (mock the `httpx` GET call rather than hitting the real API).
5. Manually re-run the reproduction script against a real repo and confirm `has_tests` now appears correctly.

### Inputs & outputs
**Input:** a repo path or repo file listing (already available).
**Output:** the existing analysis output dict/object, now including one additional field: `has_tests: bool`.

### Risks & unknowns
- The GitHub contents API only lists root-level entries by default — a `test_*.py` file nested in a subfolder (not inside a `tests/` dir) would be missed unless I add a recursive call, which costs extra API requests and could hit rate limits (the tool already handles 403/rate-limit errors, so this needs to stay within that budget).
- Case sensitivity / naming variants (e.g. `Tests/`, `spec/`, `__tests__/` for JS-style repos) aren't covered by the issue's stated detection rules — need to decide whether to go strictly by what's specified (tests/test dir, pytest.ini, test_*.py) or generalize later.
- `_fetch_repo_metadata` already makes one extra HTTP call for `_has_readme`; adding `_has_tests` means a second extra call per analysis, which adds latency and another failure point to handle gracefully (e.g. contents endpoint 404 on an empty repo).
- Confirmed the output is a plain dict, not a dataclass/pydantic model, so adding a new key is low-risk for existing consumers — but should still check if `market_analyzer.py` or `skill_extractor.py` assume a fixed set of keys anywhere.
- Discovered a pre-existing mypy error in `_has_readme` (`github_tool.py:135`, "Returning Any from function declared to return bool") that surfaced only once a test started importing this module through the strict `mypy` pre-commit hook. Not caused by this change, and out of scope to fix this week, but `_has_tests` should be written carefully (likely with an explicit `bool(...)` cast) to avoid introducing the same issue.

### Edge cases
- Repo with an empty `tests/` directory (no actual test files inside) — still counts as `has_tests: true`, or should it require files inside?
- Repo with a `test_*.py` file at the root but no `tests/` folder.
- Repo with a `pytest.ini` but no test files at all (misconfigured repo).
- Very large repos — performance of listing/searching for test indicators shouldn't blow up runtime.
