cat > PLAN.md <<'EOF'
## Solution plan

**Issue:** [Add a `has_tests` boolean to the repo analysis output](https://github.com/ascherj/pathreview/issues/50)

### Understand

`GitHubTool` in `agent/tools/github_tool.py` fetches information about a GitHub repository and returns metadata such as the repository name, primary language, star count, fork count, open issue count, and whether the repository contains a README.

The root cause is that `GitHubTool._fetch_repo_metadata()` only requests the basic repository information and checks for a README. It does not inspect the repository file tree, so it cannot determine whether test files or test folders exist. Its returned metadata dictionary also does not contain a `has_tests` key.

I reproduced the gap by running `GitHubTool.execute()` against the PathReview repository. The request succeeded and returned `has_readme: True`, but checking `"has_tests" in result.data` returned `False`.

Expected behaviour:

- Return `has_tests: True` when the repository contains recognised test indicators.
- Return `has_tests: False` when no recognised test indicators are found.

Actual behaviour:

- The `has_tests` field is missing entirely from the metadata returned by `GitHubTool`.

There is already similar test-detection logic in `ingestion/parsers/repo_analyzer.py`, but that parser is separate from the agent GitHub tool. The GitHub tool still needs access to repository file paths and must include the Boolean result in its own output.

### Map

The following codebase parts are involved:

- `agent/tools/github_tool.py`
  - `GitHubTool.execute()`
  - `GitHubTool._fetch_repo_metadata()`
  - `GitHubTool._has_readme()`
  - A new `_has_tests()` helper will likely be added.
  - A separate helper for fetching the repository tree may also be added.

- `ingestion/parsers/repo_analyzer.py`
  - `RepoAnalyzer._detect_tests()`
  - This existing method provides a useful reference for recognised test indicators.
  - This file may not need to be modified because it belongs to a different analysis path.

- `tests/unit/test_github_tool.py`
  - This will be a new unit test file.
  - It will test the new test-detection behaviour without making real GitHub network requests.

The GitHub API paths involved will likely include:

- `/repos/{username}/{repo_name}` for repository metadata and the default branch.
- `/repos/{username}/{repo_name}/git/trees/{branch}?recursive=1` for repository file paths.

### Plan

1. Update `GitHubTool._fetch_repo_metadata()` to read the repository's `default_branch` from the basic GitHub repository response instead of assuming the branch is named `main`.

2. Add a helper that requests the repository tree from GitHub using the default branch and extracts the returned file and folder paths.

3. Add a private `_has_tests()` helper that examines the repository paths and returns `True` when it finds one of the required indicators:
   - a `tests/` directory
   - a `test/` directory
   - a `pytest.ini` file
   - a Python file whose filename matches `test_*.py`

4. Call `_has_tests()` from `_fetch_repo_metadata()` and add the result to the returned dictionary using the key `"has_tests"`.

5. Create `tests/unit/test_github_tool.py` and mock the GitHub API responses. Add tests for repositories with tests, repositories without tests, nested test directories, different default branches, and GitHub request failures.

### Inputs & outputs

Inputs to `GitHubTool.execute()`:

- `github_username`
- `repo_name`

Additional data used internally:

- Repository metadata returned by GitHub
- The repository's default branch
- Repository file and folder paths returned by the GitHub tree API
- An optional GitHub API token already supported by `GitHubTool`

Output:

`GitHubTool.execute()` should continue returning a `ToolResult`. Its `data` dictionary should contain all existing metadata fields and one additional Boolean field:

- `"has_tests": True` when recognised tests are found
- `"has_tests": False` when recognised tests are not found

The change should not remove or rename existing metadata fields such as `has_readme`, `primary_language`, or `star_count`.

### Risks & unknowns

- The GitHub recursive tree API may return `"truncated": true` for very large repositories. In that case, some test files may not appear in the response.

- Fetching the repository tree requires an additional GitHub API request. Unauthenticated requests have stricter rate limits, so repeated repository analysis may receive a `403` response.

- Repositories may use default branches such as `master`, `develop`, or another custom name. The implementation must use the `default_branch` value returned by GitHub rather than assuming `main`.

- Private repositories may not be accessible without a valid API token.

- Returning `False` when the GitHub tree request fails could make “unable to inspect” look the same as “no tests found.” I need to confirm whether this is acceptable or whether the failure should be logged separately while preserving the existing `ToolResult` behaviour.

- Test-detection logic already exists in `ingestion/parsers/repo_analyzer.py`. Duplicating similar matching rules in `GitHubTool` could cause the two implementations to behave differently later. I need to decide whether the logic can be shared safely without creating unnecessary coupling between the agent and ingestion modules.

- A broad search for the text `test_` could create false positives. Detection should examine complete path segments or filenames instead of matching unrelated words anywhere in a path.

### Edge cases

- A repository containing a root-level `tests/` directory
- A repository containing a root-level `test/` directory
- A nested test directory such as `backend/tests/`
- A root-level `pytest.ini` file
- A nested Python test file such as `src/tests/test_api.py`
- A root-level Python test file such as `test_app.py`
- A repository containing no test files or folders
- An empty repository
- A repository whose default branch is not `main`
- A repository tree response marked as truncated
- A private or unavailable repository
- A GitHub `403` rate-limit response
- A GitHub `404` response
- A request timeout or network failure
- Unrelated filenames such as `latest_update.py`, `contest_results.py`, or `testing_notes.md`, which should not automatically count as test files
EOF