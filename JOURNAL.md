## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/53

**Issue title:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's agent system can analyze repository information, but it does not currently check whether a project's declared dependencies are significantly outdated. Issue #53 asks for a new `DependencyAuditTool` that parses supported dependency files such as `requirements.txt`, `package.json`, and `pyproject.toml`, then flags dependencies that are more than one major version behind the current release. The tool will follow PathReview's existing agent tool structure and be integrated with the orchestrator. A successful fix will provide useful dependency freshness information without failing on unsupported or malformed dependency specifications.

**Branch name:** feat/53-dependency-audit-tool

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection reasoning:**
I chose this Tier 2 issue because, although the overall PathReview codebase was initially unfamiliar to me, the scope of this issue is bounded enough for me to reason about after tracing the existing agent tool structure. I reviewed `BaseTool`, existing tools such as `ReadmeScorer`, the agent orchestrator, and adjacent unit tests, and I was able to identify a clear implementation path: add one new dependency-audit tool, integrate it with the orchestrator, and test its behavior. I chose it over a simpler Tier 1 issue because it gives me experience working across multiple parts of the agent system while still having a defined feature boundary.
