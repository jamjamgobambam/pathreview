# Solution plan

**Issue:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos —
https://github.com/ascherj/pathreview/issues/53

### Understand

This is a **feature gap**, not a bug — there is no incorrect behavior to fix, the
capability simply does not exist. PathReview's agent can already detect a repo's
tech stack (`agent/tools/tech_detector.py`), but nothing reads a project's
dependency manifests and reports which dependencies are badly out of date.

- **Expected:** the agent can look at a repo's `requirements.txt`, `package.json`,
  and/or `pyproject.toml`, compare each declared dependency against its latest
  published release, and flag any dependency that is more than one major version
  behind. This supports the DevOps/CI use case of surfacing maintenance risk.
- **Actual:** importing `agent.tools.dependency_audit_tool` raises
  `ModuleNotFoundError`; there are zero references to dependency/version auditing
  anywhere under `agent/`. Reproduced by the failing test
  `tests/unit/test_dependency_audit_tool.py` (commit `39da983`).

### Map

Files I expect to touch:

| File | Change |
|---|---|
| `agent/tools/dependency_audit_tool.py` | **New.** `DependencyAuditTool(BaseTool)` — parse manifests, compare versions, return findings. |
| `agent/orchestrator.py` | Register the tool: add a branch in `_build_plan()` that queues `dependency_audit` when manifests are available. (Note: `Orchestrator` is not yet instantiated anywhere, so the tools-dict wiring point does not exist yet — the plan branch is the registration site, matching `docs/CONTRIBUTING.md`.) |
| `tests/unit/test_dependency_audit_tool.py` | Expand the reproduction into a full unit suite once the I/O contract is final. |
| `tests/fixtures/` | **New.** Sample `requirements.txt` / `package.json` / `pyproject.toml` and mock registry responses. |

Reference implementations to mirror: `agent/tools/tech_detector.py` (same
`BaseTool` shape, manifest-name awareness) and `agent/tools/github_tool.py` (how
the codebase calls an external API + mocks it in tests).

### Plan

1. **Parsers.** Add three pure functions that turn manifest text into
   `(name, current_version, ecosystem)` records: `requirements.txt` (line-based),
   `package.json` (`json` — `dependencies` + `devDependencies`), `pyproject.toml`
   (`tomllib`, PEP 621 `[project].dependencies` and `[tool.poetry.dependencies]`).
2. **Latest-version resolver.** Define a small resolver interface with two
   implementations: an injectable dict (used by tests, and accepted via
   `input_data["latest_versions"]`) and a live one that queries the PyPI JSON API
   / npm registry using the already-installed `requests`. Injection keeps the tool
   deterministic and offline-testable.
3. **Comparison + flagging.** Normalize versions, extract the major component
   (strip `^`/`~`/`>=` for npm; use `packaging.version` for Python), compute
   `majors_behind = latest.major - current.major`, and flag when it exceeds the
   configurable `max_major_lag` (default 1, i.e. flag when ≥2 majors behind).
4. **Tool wrapper.** Implement `execute(input_data)` returning
   `ToolResult(success, data)` with the output shape below; catch and log parse
   errors per-manifest so one bad file never fails the whole run.
5. **Register + test.** Add the `_build_plan()` branch in `orchestrator.py`, expand
   the unit suite (mark `@pytest.mark.unit`), and run `make check && make test-unit`.

### Inputs & outputs

- **Input:** `{"manifests": {"<filename>": "<raw text>", ...},
  "latest_versions"?: {"<pkg>": "<version>"}, "max_major_lag"?: int}`. The
  orchestrator will populate `manifests` from fetched repo files.
- **Output:** `ToolResult(success=True, data={
    "outdated": [{"name", "ecosystem", "current", "latest", "majors_behind"}],
    "checked": int, "skipped": [{"name"|"file", "reason"}]
  })`. On a hard failure: `ToolResult(success=False, data={}, error=str)`.

### Risks & unknowns

- **Getting "latest version" reliably.** Live registry calls add network/rate-limit
  flakiness and don't work offline/in CI. Mitigation: resolver is injectable and
  tests never hit the network; live fetch is best-effort with timeout + graceful
  skip.
- **Threshold semantics.** "More than one major version behind" — I read this as
  ≥2 majors behind (`majors_behind > 1`), made configurable via `max_major_lag`.
  **Open question for the maintainer:** is 1 major behind already "outdated"?
- **Version-range parsing.** npm ranges (`^`, `~`, `*`, `>=`, `workspace:`, git/file
  URLs) and Python markers/extras/VCS pins are messy; unparseable specs are
  skipped, not guessed.
- **0.x versions**, where a major bump is not the usual SemVer signal.

### Edge cases

- No/empty `manifests` → `success=True`, `outdated=[]` (never crash).
- Malformed manifest (bad JSON/TOML, junk lines) → skip that file with a recorded
  reason, keep processing the others.
- Comments, blank lines, `-r`/`-e` includes, extras (`pkg[extra]==1.0`), and
  environment markers (`; python_version < "3.8"`) in `requirements.txt`.
- Unpinned or range-only deps with no resolvable current version → skipped.
- PEP 503 name normalization so `Django` and `django` compare equal.
- Pre-release / non-numeric versions handled without throwing.
