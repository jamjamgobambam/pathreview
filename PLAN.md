## Solution plan

**Issue:** [Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos](https://github.com/ascherj/pathreview/issues/53)

### Understand

PathReview currently detects technologies from repository file names, but it does not inspect project dependency files or report packages that are significantly outdated. The existing `GitHubTool` retrieves repository metadata only, while `TechDetector` receives file paths without their contents. There is also no `dependency_audit` tool in the agent system or corresponding entry in the orchestrator’s execution plan.

The expected behavior is for PathReview to inspect supported dependency manifests, determine the declared dependency versions, compare them with current package-registry releases, and flag dependencies whose latest major version is more than one major version ahead of the project’s declared version. For example, a project using version 1.x when version 3.x is current should be flagged, while a project using version 2.x when version 3.x is current should not be flagged.

### Map

Files expected to be added or modified:

- `agent/tools/dependency_audit_tool.py`
  - New `DependencyAuditTool` implementation.
  - Parsing logic for Python and npm dependency manifests.
  - GitHub manifest retrieval and package-registry version lookup.
  - Major-version comparison and structured result generation.

- `agent/orchestrator.py`
  - Add `dependency_audit` to the execution plan when a profile contains a GitHub project.
  - Pass the GitHub username and repository name to the tool.

- `tests/unit/test_dependency_audit_tool.py`
  - Expand the reproduction test into unit tests for parsing, version comparison, missing files, malformed content, and mocked API responses.

- Potentially `tests/fixtures/`
  - Add mock GitHub, PyPI, or npm responses only if keeping the response data inside the test file makes the tests difficult to read.

The following existing code provides the implementation patterns:

- `agent/tools/base.py`
- `agent/tools/github_tool.py`
- `agent/tools/tech_detector.py`
- `agent/orchestrator.py`
- `tests/unit/test_tech_detector.py`

### Plan

1. Implement the `DependencyAuditTool` using the existing `BaseTool` and `ToolResult` interface. Define an input contract that accepts a GitHub username and repository name, while also allowing dependency-file contents to be supplied directly for isolated unit testing.

2. Add helpers that retrieve supported root-level manifest files from GitHub and parse:
   - `requirements.txt`
   - `package.json`
   - `pyproject.toml`

   Use Python’s built-in `json` and `tomllib` modules where possible, and conservatively skip dependency entries that do not contain a usable numeric version.

3. Add package-registry lookup helpers using `httpx`. Python dependencies will be checked against PyPI, and JavaScript dependencies will be checked against npm. Compare the declared and current major versions and flag a dependency only when the difference is greater than one.

4. Update `Orchestrator._build_plan()` so that a `dependency_audit` task is added for the first submitted GitHub project, following the existing behavior of `github_tool`. Pass `github_username` and `repo_name` as the tool input.

5. Add unit tests with mocked HTTP responses. Cover each supported manifest format, outdated and current dependencies, missing manifests, malformed input, registry failures, and the orchestrator plan entry. Run Ruff, Black, Mypy, and the unit test suite before submitting the implementation.

### Inputs & outputs

The primary tool input will contain:

- `github_username`: owner of the GitHub repository
- `repo_name`: repository to inspect

For testing and future ingestion integration, the tool may also accept:

- `dependency_files`: a mapping of file paths to file contents

Example direct input:

```python
{
    "dependency_files": {
        "requirements.txt": "fastapi==0.90.0\nhttpx==0.20.0",
        "package.json": "{\"dependencies\": {\"react\": \"^16.0.0\"}}",
    }
}
```

The tool should return a `ToolResult`. Its data should clearly report:

- Which manifest files were found and audited
- How many dependencies were checked
- Which dependencies are outdated
- Their declared and latest versions
- How many major versions behind they are
- Their package ecosystem and source manifest
- Any dependencies or files that were skipped because they could not be parsed or checked

An outdated dependency entry should resemble:

```python
{
    "name": "example-package",
    "ecosystem": "pypi",
    "declared_version": "1.4.0",
    "latest_version": "3.1.0",
    "major_versions_behind": 2,
    "source_file": "requirements.txt",
}
```

### Risks & unknowns

- The repository does not currently have a complete path for downloading manifest contents. The new tool may need to retrieve supported files through the GitHub Contents API rather than relying on `TechDetector` file paths.
- `Orchestrator` accepts a dictionary of tool instances, but no current production construction point for that dictionary exists in the repository. The issue's orchestrator integration will therefore focus on adding the tool to the execution plan without redesigning the placeholder review pipeline.
- Dependency version specifications can be complex. Examples include ranges, wildcards, Git URLs, local paths, extras, environment markers, npm aliases, and workspace dependencies. The first implementation should handle common numeric versions and skip unsupported specifications safely.
- GitHub, PyPI, and npm requests may fail because of rate limits, timeouts, unavailable packages, or private repositories. External failures should not crash the entire agent run.
- Some repositories are monorepos with manifests below the root directory. Root-level manifest support is the initial scope unless the issue owner confirms that recursive repository traversal is required.
- Scoped npm package names must be URL encoded correctly when querying the npm registry.
- Pre-release versions could produce misleading comparisons. Registry responses should use the normal latest release rather than treating every pre-release as current.

### Edge cases

The implementation should handle these cases gracefully:

- No supported dependency files are present
- The input dictionary is empty or missing repository information
- `requirements.txt` contains blank lines, comments, recursive includes, editable installs, URLs, or environment markers
- A Python dependency is unpinned or does not contain a numeric version
- `package.json` contains invalid JSON
- `package.json` has no dependency sections
- npm dependencies use `^`, `~`, wildcards, aliases, Git URLs, or workspace references
- `pyproject.toml` contains invalid TOML
- Dependencies appear under standard PEP 621 or Poetry sections
- A package does not exist in PyPI or npm
- A registry request times out or returns an invalid response
- The declared and latest versions have the same major version
- The latest version is exactly one major version ahead, which should not be flagged
- The latest version is two or more major versions ahead, which should be flagged
- The same dependency appears in more than one manifest