# Solution Plan

**Issue:** Add a `has_tests` boolean to the repo analysis output

Issue Link: https://github.com/ascherj/pathreview/issues/50

---

## Understand

The goal of this issue is to expose a `has_tests` boolean in the repository analysis output.

After inspecting the codebase, I found that `ingestion/parsers/repo_analyzer.py` already contains a `_detect_tests()` method that can detect test-related files and directories and already adds `has_tests` to its metadata.

However, `agent/tools/github_tool.py`, which retrieves repository metadata from the GitHub API, does not currently collect the repository file structure or return a `has_tests` field. Because of this, users of `GitHubTool` cannot determine whether a repository contains tests.

The expected behavior is for the repository analysis output to include a `has_tests` boolean that is `true` whenever the repository contains:

- `tests/`
- `test/`
- `pytest.ini`
- Python test files matching `test_*.py`

Otherwise, it should return `false`.

---

## Map

Files investigated:

- `agent/tools/github_tool.py`
- `ingestion/parsers/repo_analyzer.py`

Expected files to modify:

- `agent/tools/github_tool.py`

Potential supporting files:

- Existing GitHub API helper methods
- Any repository analysis or integration tests if available

---

## Plan

1. Determine how `GitHubTool` should retrieve the repository file structure from the GitHub API.
2. Reuse the existing test detection logic where possible instead of duplicating functionality.
3. Add logic to determine whether the repository contains supported test indicators.
4. Include a `has_tests` boolean in the metadata returned by `GitHubTool`.
5. Verify that repositories with and without test files return the correct value.

---

## Inputs & Outputs

### Input

- GitHub repository owner
- Repository name
- Repository contents retrieved through the GitHub API

### Output

Repository metadata containing a new field:

```json
{
  "has_tests": true
}
```

or

```json
{
  "has_tests": false
}
```

depending on whether test-related files or directories are detected.

---

## Risks & Unknowns

- `GitHubTool` currently does not retrieve the repository file structure, so additional GitHub API requests may be required.
- The existing `_detect_tests()` implementation is located in `RepoAnalyzer`; I need to determine whether it should be reused directly or whether the logic should be moved into a shared utility.
- Additional API requests could impact performance or GitHub rate limits.

---

## Edge Cases

The implementation should correctly handle:

- Repositories containing only a `tests/` directory.
- Repositories containing only a `test/` directory.
- Repositories containing only `pytest.ini`.
- Repositories containing only `test_*.py` files.
- Empty repositories.
- Repositories with no test-related files.
- Large repositories where only part of the file tree may initially be retrieved.