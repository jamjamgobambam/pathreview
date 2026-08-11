# Solution plan

**Issue:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos - https://github.com/ascherj/pathreview/issues/53

### Understand

The root cause is a feature gap in the agent tool system. PathReview can detect technologies, score READMEs, extract skills, and analyze market fit, but it does not currently have a tool that reads dependency manifest files and reports stale dependencies. The expected behavior is that the agent can inspect files such as `requirements.txt`, `package.json`, and `pyproject.toml`, compare declared dependency major versions with current major versions, and report dependencies that are more than one major version behind. The actual behavior today is that `agent.tools.dependency_audit_tool` does not exist, so the orchestrator cannot include dependency freshness findings in a project review.

### Map

Expected files to touch:

- `agent/tools/dependency_audit_tool.py` - add the new `DependencyAuditTool` class.
- `agent/tools/__init__.py` - export the new tool if the package begins collecting tool exports.
- `agent/orchestrator.py` - add the dependency audit step to `_build_plan` when repository file contents include supported dependency manifests.
- `tests/unit/test_dependency_audit_tool.py` - replace the current reproduction failure with unit tests for parsing and outdated-major-version detection.
- `tests/unit/test_tech_detector.py` or a new orchestrator-focused test - add coverage if orchestrator registration changes need direct verification.
- `tests/fixtures/` - add small sample dependency files if fixtures are clearer than inline test strings.

### Plan

1. Study the existing agent tool pattern in `agent/tools/base.py`, `agent/tools/tech_detector.py`, and `agent/tools/readme_scorer.py` so the new tool returns `ToolResult` consistently.
2. Implement `DependencyAuditTool` with parsers for `requirements.txt`, `package.json`, and `pyproject.toml`, using the standard library where possible.
3. Add version comparison logic that flags a dependency only when the declared major version is more than one behind the latest known major version.
4. Design the tool input so tests can inject dependency file contents and latest-version data without relying on live package registry calls.
5. Register the tool in `agent/orchestrator.py` so project reviews with supported dependency files can include dependency audit results.
6. Expand `tests/unit/test_dependency_audit_tool.py` to cover successful parsing, outdated dependencies, current dependencies, unsupported files, and malformed files.

### Inputs & outputs

Inputs:

- `DependencyAuditTool.execute(input_data: dict)` should accept a dictionary with dependency file contents, for example `{"files": {"requirements.txt": "fastapi==0.90.0", "package.json": "{...}"}}`.
- Supported dependency file contents keyed by filename, such as `requirements.txt`, `package.json`, or `pyproject.toml`.
- A latest-version source or injected mapping for tests, such as `{"react": "19.0.0", "fastapi": "0.115.0"}`, so `tests/unit/test_dependency_audit_tool.py` can run without network access.

Outputs:

- A `ToolResult` from `agent/tools/base.py` with `success=True` when parsing completes and `success=False` only for unexpected tool-level failures.
- A data payload shaped like `{"audited_dependencies": [...], "outdated_dependencies": [...], "skipped_files": [...], "warnings": [...]}`.
- Each outdated dependency finding should include the package name, source file, declared version, latest known version, and the major-version gap.
- Findings that `agent/orchestrator.py` can merge into the agent's overall project review under a `dependency_audit` tool result.

### Risks & unknowns

- `agent/orchestrator.py::_build_plan()` currently receives file paths through `profile_data["files"]`, but issue #53 requires parsing file contents. I need to confirm where repository file contents are available or whether `agent/tools/github_tool.py` output should feed this tool.
- Live package registry calls inside `agent/tools/dependency_audit_tool.py` could make tests slow or flaky. I plan to keep version lookup injectable and mock it in `tests/unit/test_dependency_audit_tool.py`.
- Python dependency parsing in `agent/tools/dependency_audit_tool.py` can include version ranges, extras, comments, environment markers, and unpinned packages. The first implementation should handle common pinned/ranged cases gracefully and skip ambiguous cases with a warning.
- `pyproject.toml` dependencies can appear under `[project]` or tool-specific sections such as Poetry. I need to decide which sections `DependencyAuditTool` will support in the first pass and document skipped sections in the tool output.

### Edge cases

- Missing dependency files should return a successful result with no findings, not crash the agent.
- Unsupported files should be listed as skipped.
- Malformed `package.json` or `pyproject.toml` should produce a warning and continue auditing other files.
- Dependencies without a declared major version, such as unpinned requirements, should not be falsely flagged.
- Pre-release or non-standard versions should be skipped or reported as unknown instead of breaking execution.
- Duplicate dependencies across files should be deduplicated or reported clearly so the agent review does not repeat the same finding.
