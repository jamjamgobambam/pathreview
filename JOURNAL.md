## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/53

**Issue title:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**

PathReview currently identifies technologies used in a repository, but it does not check whether the project depends on packages that are significantly outdated. This issue requires a new agent tool that reads dependencies from `requirements.txt`, `package.json`, and `pyproject.toml`, compares their versions with current releases, and flags packages that are more than one major version behind. The tool must follow the existing `BaseTool` structure and be connected to the agent orchestrator. A successful fix will produce clear dependency audit results and include tests for the supported file types and error cases.

**Branch name:** `feat/53-dependency-audit-tool`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue fit and selection reasoning

I selected this Tier 2 issue because it requires understanding how the agent tools and orchestrator work together, but it is still limited to a clearly defined feature. I reviewed `agent/tools/base.py`, `agent/tools/tech_detector.py`, `agent/tools/readme_scorer.py`, `agent/orchestrator.py`, and the existing unit tests for `TechDetector`. My experience with Python, APIs, testing, and agent-based applications makes the scope realistic for me. The issue has no listed blockers or unresolved dependencies, and I believe it can be completed and tested within Weeks 8 and 9.