## Solution plan

**Issue:** [Add a `has_tests` boolean to the repo analysis output](https://github.com/ascherj/pathreview/issues/50)

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
The `_fetch_repo_metadata()` function in `agent/tools/github_tool.py` never determines whether a repository has tests. It returns metadata like name, stars, language, and `has_readme`, but no test-coverage signal at all. Expected: the analysis output includes `has_tests: True` for a repo that contains a `tests/` directory, a `pytest.ini`, or `test_*.py` files. Actual: there is no `has_tests` field in `GitHubTool`'s output.

### Map
<!-- Which files, functions, or modules are involved?
List the specific files you expect to touch. -->
`agent/tools/github_tool.py` and `ingestion/parsers/repo_analyzer.py` are both involved, but no changes need to be made to `repo_analyzer.py` — the `has_tests` boolean already exists in its output and the detection logic already exists in its `_detect_tests()`. The two files are separate subsystems and no live code path connects them, so the fix stays entirely in `github_tool.py`.

Files to touch:
- `agent/tools/github_tool.py` — the file we change.
  - Add a new `_detect_tests(username, repo_name, default_branch) -> bool` method, modeled on the existing `_has_readme()` method.
  - In `_fetch_repo_metadata()`, capture `default_branch` from the API response and add `"has_tests": self._detect_tests(...)` to the returned `metadata` dict, next to `has_readme`.
- `tests/unit/test_github_tool.py` — add a unit test with a mocked GitHub tree response.

Deliberately not changed:
- `ingestion/parsers/repo_analyzer.py` — its `_detect_tests()` and `has_tests` output already exist and are out of scope. We are not wiring the ingestion pipeline to `GitHubTool` (that is a separate, currently-dead code path).

### Plan
<!-- What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. Add a `_detect_tests()` method to `GitHubTool` that fetches the repository's recursive git tree (`GET /repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1`) and returns `True` if any path indicates tests: a `tests/` or `test/` directory, a `pytest.ini`, or a `test_*.py` file. Reuse the auth-header and try/except-returns-False style from `_has_readme()`.
2. In `_fetch_repo_metadata()`, read `default_branch` from the API response (`repo_json.get("default_branch", "main")`) and add `"has_tests"` to the returned `metadata` dict.
3. Add a unit test that mocks the tree endpoint and asserts `has_tests` is `True` when test paths are present and `False` when they are not.
4. Run the test suite and confirm no regressions in existing `GitHubTool` behavior.

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
- Input: a `github_username` and `repo_name` (same as the tool already takes), plus the repo's `default_branch` obtained from the existing API response.
- Network input: the GitHub git-tree API response (list of path entries).
- Output change: `GitHubTool`'s returned metadata dict gains a `has_tests: bool` field alongside `has_readme`. No change to any other field or to `repo_analyzer.py`.

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
- Extra API call: detecting tests requires one more GitHub request per repo, adding latency and consuming rate limit. The tool already handles 403 (rate-limited) at the `execute()` level; `_detect_tests()` should fail safe to `False` on any error rather than raising.
- Truncated trees: the git-tree API sets a `truncated` flag for very large repos, so test files could be missed. Acceptable for a portfolio signal, but worth noting.
- Duplicated logic: test detection now exists in two places (`GitHubTool` and `RepoAnalyzer._detect_tests`). This is deliberate — they consume different inputs — but should be called out so it isn't read as an accidental divergence.
- Default branch assumption: repos may not use `main`; we take `default_branch` from the API response and fall back to `"main"` only if it is absent.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
- Repo with no tests → `has_tests: False`.
- Empty repo / no default branch / tree fetch fails or times out → `has_tests: False` (fail safe, no exception).
- Tests present only as root-level `test_*.py` files or `pytest.ini` (no `tests/` dir) → still `True`.
- Case sensitivity: match paths case-insensitively (`Tests/`, `TEST_foo.py`).
- Directory named like a test but not one (e.g. `contest/`, `latest/`) → must not false-positive; match on `tests/` / `test/` path boundaries, not a bare `test` substring.
- Missing API token (unauthenticated request) → still works, just under stricter rate limits.
