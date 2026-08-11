# Issue #53 Solution Plan

**Issue:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos

**Issue link:** https://github.com/ascherj/pathreview/issues/53

## Understand

PathReview currently has no agent tool that evaluates whether a submitted repository's declared dependencies are significantly outdated. My reproduction confirmed that `agent/tools/dependency_audit_tool.py` does not exist and that `Orchestrator._build_plan()` does not schedule dependency auditing even when `requirements.txt` and `package.json` appear in the repository file list.

A correct implementation should add a `DependencyAuditTool` that supports `requirements.txt`, `package.json`, and `pyproject.toml`, determines the declared major version of each dependency, compares it with the current released major version, and flags dependencies that are more than one major version behind. The tool should follow the existing `BaseTool` / `ToolResult` contract and be included in the agent execution plan for repository-backed projects.

The fix is complete when supported manifests can be audited without crashing, dependencies zero or one major version behind are not flagged, dependencies more than one major version behind are flagged, malformed or unsupported dependency specifications are handled safely, and unit tests plus the project checks pass.

## Map

The main files involved are:

- `agent/tools/dependency_audit_tool.py` — new tool containing dependency manifest parsing, version comparison, and audit behavior.
- `agent/tools/base.py` — defines the `BaseTool` interface and `ToolResult` structure that the new tool must follow. No change is expected unless implementation reveals a missing shared capability.
- `agent/orchestrator.py` — `Orchestrator._build_plan()` will need to schedule the dependency audit when repository information is available.
- `agent/tools/github_tool.py` — reference for the existing GitHub API, `httpx`, timeout, and graceful error-handling patterns.
- `agent/tools/tech_detector.py` — shows that the current `files` input contains repository file paths and can recognize dependency-manifest filenames, but does not contain the manifest contents needed for an audit.
- `ingestion/parsers/repo_analyzer.py` — currently detects technology/config-file presence from repository metadata and `file_structure`, but does not inspect dependency versions.
- `tests/unit/test_dependency_audit_tool.py` — new unit tests for parsing, comparison, error handling, and output.
- `tests/unit/test_orchestrator.py` — new focused tests for scheduling the dependency audit from `_build_plan()` because no dedicated orchestrator unit test file currently exists.

## Plan

1. Trace the manifest-content input path before implementing the tool. I will inspect how `profile_data` is constructed and where the `tools` dictionary passed to `Orchestrator` is assembled. The current orchestrator only receives a list of file names for `tech_detector`, so I need to confirm the smallest change that gives the new tool access to actual manifest contents.

2. Create `agent/tools/dependency_audit_tool.py` with a `DependencyAuditTool(BaseTool)` implementation. The tool will expose the standard `execute(input_data)` method and return a `ToolResult`. Parsing logic will be separated into helper methods so `requirements.txt`, `package.json`, and `pyproject.toml` can be tested independently.

3. Implement parsing for the three supported manifest types. `requirements.txt` parsing will extract package names and version specifications from usable requirement lines. `package.json` parsing will inspect dependency entries. `pyproject.toml` parsing will inspect standard Python project dependency declarations and any project-supported layout identified during implementation.

4. Add a version-resolution layer that determines the current released version of each package. The proposed approach is to use PyPI for Python dependencies and the npm registry for JavaScript dependencies, following the existing `httpx` request/error-handling style in `GitHubTool`. The resolver will be isolated behind a helper or injectable boundary so unit tests can provide deterministic versions without depending on live network requests.

5. Compare the declared and current major versions. A dependency will only be added to the outdated list when `latest_major - declared_major > 1`. Exactly one major version behind will not be flagged.

6. Integrate the tool with `Orchestrator._build_plan()`. For a project with repository information, the plan should include a `dependency_audit` step with the repository or manifest input established in step 1. The tool should remain independent from unrelated RAG, safety, or review-generation code.

7. Add `tests/unit/test_dependency_audit_tool.py` covering all three manifest formats, the major-version threshold, no-outdated-dependency behavior, malformed input, unsupported version specifications, missing manifests, and failed version lookups. Follow the existing pytest/tool testing pattern used by files such as `tests/unit/test_readme_scorer.py`.

8. Add an orchestrator unit test confirming that a repository-backed project schedules the dependency-audit tool and that profiles without usable repository/dependency information do not schedule it unnecessarily.

9. Run the targeted new tests first, then `make test-unit` and `make check`. Fix any regressions before opening the Week 9 pull request.

## Inputs & Outputs

### Planned external input

The preferred input for the agent tool is repository identity already available to the agent flow:

    {
        "github_username": "example-user",
        "repo_name": "example-project"
    }

If tracing the current data flow shows that manifest contents are already available before agent execution, the tool will instead accept those contents directly rather than performing a duplicate GitHub fetch. I will resolve this boundary before implementation and update this plan if the actual code path requires a different shape.

### Internal manifest data

Parsing helpers should work with content equivalent to:

    {
        "requirements.txt": "...",
        "package.json": "...",
        "pyproject.toml": "..."
    }

Only manifests that actually exist need to be present.

### Output

Successful execution should return a `ToolResult` whose data makes the audit understandable to downstream code. The planned structure is:

    {
        "outdated_dependencies": [
            {
                "name": "example-package",
                "declared_version": "1.4.0",
                "latest_version": "4.2.0",
                "major_versions_behind": 3,
                "source_file": "requirements.txt"
            }
        ],
        "checked_count": 1,
        "manifest_files": ["requirements.txt"]
    }

If no dependency is more than one major version behind, `outdated_dependencies` should be an empty list rather than an error.

## Risks & Unknowns

1. **Manifest contents are not currently present in `Orchestrator._build_plan()` input.** `agent/tools/tech_detector.py` receives file names only. I need to trace the producer of `profile_data` and the construction of the orchestrator tool dictionary before deciding whether `DependencyAuditTool` should fetch manifests through the GitHub Contents API or receive their contents from an earlier layer.

2. **The issue says "current release" but does not specify version-registry behavior.** Live PyPI/npm lookups can timeout, rate-limit, return missing packages, or expose prereleases. I will isolate version lookup so failures for one dependency do not crash the entire audit and so unit tests can mock the current version.

3. **Dependency version syntax is not always a single exact version.** Python requirements can contain operators, environment markers, URLs, editable installs, wildcards, or local paths, while npm supports caret, tilde, ranges, tags, Git URLs, and workspace references. The audit should avoid inventing a major version when one cannot be determined reliably.

4. **`pyproject.toml` has multiple dependency layouts.** Standard `[project]` dependencies and tool-specific layouts such as Poetry may represent dependencies differently. I will inspect the expected project formats before deciding how much of each layout belongs in the initial implementation.

5. **The live application does not appear to pass results from one agent tool directly into the next inside `_build_plan()`.** If manifest discovery depends on `GitHubTool` output, I will avoid a broad orchestrator redesign and choose the smallest input boundary that satisfies Issue #53.

## Edge Cases

- A repository contains none of the three supported manifest files. The tool should return successfully with no outdated dependencies rather than crash.
- A dependency is exactly one major version behind the current release. It should not be flagged because the issue specifies more than one major version behind.
- A dependency is two or more major versions behind. It should be flagged with the declared version, latest version, and difference.
- `package.json` or `pyproject.toml` is malformed. The bad manifest should be handled gracefully instead of terminating the entire agent run.
- `requirements.txt` contains blank lines, comments, environment markers, Git/local-path dependencies, or a version specification from which a major version cannot be determined. Unsupported entries should be skipped or reported without creating a false positive.
- A registry lookup returns 404, times out, or is rate-limited for one package. Other dependencies should still be audited.
- A package is already on the current major version or appears newer than the registry result. It should not be flagged.
- An npm package uses a scoped name such as `@scope/package`; parsing and version lookup should preserve the complete package name.
- The same dependency appears in more than one supported manifest. The output should avoid misleading duplicate warnings or clearly preserve which source file produced each result.
