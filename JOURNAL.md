# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/53

**Issue title:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's agent can analyze submitted project repositories, but it currently
has no way to tell whether a project's dependencies are out of date. This issue
asks for a new `DependencyAuditTool` that parses common dependency manifests —
`requirements.txt`, `package.json`, and `pyproject.toml` — and flags any
dependency that trails its latest release by more than one major version. The
tool lives in `agent/tools/dependency_audit_tool.py`, implements the existing
`BaseTool` interface, and is registered with the agent in `agent/orchestrator.py`.
A successful fix gives the agent a reusable signal for dependency health across
both the Python and Node.js ecosystems, surfacing maintenance risk that today
goes undetected. This work touches the agent/tooling layer rather than the
ingestion pipeline or the frontend.

**Branch name:** feat/53-dependency-audit-tool

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/valy03/pathreview-vanly/commit/39da98339a06b87f18b4cd3ab0f6eebfaeefa9c9

**Reproduction summary:**
Because #53 is a feature gap (not a bug), I reproduced it by adding a failing
unit test, `tests/unit/test_dependency_audit_tool.py`. Running it fails at
collection with `ModuleNotFoundError: No module named
'agent.tools.dependency_audit_tool'`, confirming the tool is absent — and a
codebase search found zero dependency/version-auditing logic anywhere under
`agent/`, so the gap is exactly where the issue says it is.

**PLAN.md link:** https://github.com/valy03/pathreview-vanly/blob/feat/53-dependency-audit-tool/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
- Threshold semantics: does "more than one major version behind" mean ≥2 majors
  behind (my current reading), or is being 1 major behind already "outdated"?
  Planning to make it configurable and confirm with the maintainer.
- How to obtain each dependency's latest version — live PyPI/npm registry calls
  (network/CI flakiness) vs. an injected version map. Leaning toward an injectable
  resolver with a best-effort live fallback so tests stay offline/deterministic.
