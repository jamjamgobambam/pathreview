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
