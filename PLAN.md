## Solution plan

**Issue:** [Add a `has_tests` boolean to the repo analysis output](https://github.com/ascherj/pathreview/issues/50)

### Understand

`GitHubTool._fetch_repo_metadata()` in `agent/tools/github_tool.py` fetches general repository metadata and checks for a README, but it never fetches or examines the repository file tree. As a result, `GitHubTool.execute()` omits `has_tests` even when a repository contains an indicator named in the issue, such as `tests/test_example.py`. The expected behavior is for successful repository analysis to include a boolean `has_tests` field that is `True` when the repository contains a `tests/` or `test/` directory, a `pytest.ini` file, or a Python file whose basename matches `test_*.py`, and `False` otherwise.

The issue also names `agent/tools/repo_analyzer.py`, but that file does not exist on this branch. The current repository-analysis path is `agent/orchestrator.py` → `GitHubTool.execute()` → `GitHubTool._fetch_repo_metadata()`, with the returned dictionary stored under `tool_results["github_tool"]`.

### Map

- `agent/tools/github_tool.py`: fetch the repository tree, detect the issue's test indicators, and add `has_tests` to the returned metadata.
- `tests/unit/test_github_tool.py`: replace the reproduction-only coverage with a complete unit-test matrix for positive, negative, and API-error cases.
- `agent/orchestrator.py`: verify that the existing pass-through behavior exposes `has_tests`; change it only if an orchestrator-level test shows the field is dropped or transformed.

### Plan

1. Add a private helper in `agent/tools/github_tool.py` that requests the GitHub recursive tree for the repository's default branch and returns normalized repository paths.
2. Add a focused path-matching helper that recognizes `tests/` and `test/` path components, a `pytest.ini` basename, and Python basenames matching `test_*.py`, without treating partial names such as `contest/` as test directories.
3. Call the helper from `_fetch_repo_metadata()` and include the resulting boolean as `metadata["has_tests"]`, reusing the existing authentication headers and request timeouts.
4. Expand `tests/unit/test_github_tool.py` to cover every accepted indicator, a repository without tests, nested paths, near-match false positives, the default branch name, and GitHub tree-request failures or truncated responses.
5. Run the focused GitHub-tool tests and the full unit suite, then inspect an orchestrator result to confirm `tool_results["github_tool"]["has_tests"]` reaches the public analysis output unchanged.

### Inputs & outputs

The fix takes the existing `github_username` and `repo_name` inputs supplied to `GitHubTool.execute()`. It also uses the repository metadata response's `default_branch` to request that branch's recursive Git tree. A successful result should preserve all existing metadata fields and add exactly one boolean field: `has_tests: True` when any supported indicator is present and `has_tests: False` when none is present.

### Risks & unknowns

- GitHub's recursive tree response can set `truncated: true` for large repositories. `agent/tools/github_tool.py` may need pagination or a documented conservative fallback so `False` does not incorrectly mean “no tests” when the tree was incomplete.
- A second GitHub API request increases rate-limit exposure and latency. The implementation must preserve the current token header and distinguish a tree-fetch failure from a confirmed `has_tests: False`; the desired fallback behavior should be confirmed with maintainers.
- Git path matching is case-sensitive, but repositories may contain variants such as `Tests/` or `TEST/`. The issue lists lowercase indicators, so case-insensitive matching should be confirmed before broadening the specification.
- `agent/tools/repo_analyzer.py` is named in the issue but absent from the branch. Before adding a new module, check current upstream history or maintainer guidance; the existing `GitHubTool` plus orchestrator pass-through may be the intended scope.
- The existing mypy hook currently flags `agent/tools/github_tool.py:135` for returning `Any` from `_has_readme()`. Editing that file may require a small type-safe cleanup or a separately scoped upstream fix so all hooks pass.

### Edge cases

- An empty repository or a repository with no supported test indicators should return `has_tests: False`.
- Root and nested `tests/` or `test/` directories should return `True`, including an empty directory if Git represents it through a tracked placeholder file.
- Root or nested `pytest.ini` and Python files such as `test_api.py` should return `True`.
- Near matches such as `contest/`, `testing/`, `pytest.ini.example`, `test_helper.js`, and `helper_test.py` should remain `False` under the issue's exact rules.
- Non-default branch names, including names containing `/`, must be URL-safe and must not be hard-coded to `main` or `master`.
- Missing repositories, private repositories without access, rate limits, timeouts, malformed tree payloads, and truncated trees should preserve the tool's existing error contract and must not silently report a confidently false result.
