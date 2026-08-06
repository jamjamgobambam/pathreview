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


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [test:reproduce missing dependency audit tool](https://github.com/dinakarbl00/pathreview/commit/d972ea935c78f46f4d91f4d2ca3eee390a66f40f)

**Reproduction summary:**
I reproduced the feature gap by adding a unit test that checks whether the `agent.tools.dependency_audit_tool` module exists. The test failed because the module has not yet been implemented, confirming that PathReview currently has no agent tool for auditing outdated project dependencies.

**PLAN.md link:** [PLAN.md](https://github.com/dinakarbl00/pathreview/blob/feat/53-dependency-audit-tool/PLAN.md)

**Blockers or open questions:**
The main open question is how the tool should obtain the contents of dependency manifest files. The existing GitHub tool retrieves repository metadata but does not download `requirements.txt`, `package.json`, or `pyproject.toml`, so the implementation may need to use the GitHub Contents API while keeping the work within issue #53’s Tier 2 scope.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I implemented the new `DependencyAuditTool` using the existing `BaseTool` and `ToolResult` structure. The tool supports `requirements.txt`, `package.json`, and `pyproject.toml`, retrieves root-level dependency manifests from GitHub when repository details are provided, checks current versions through PyPI and npm, and flags packages that are more than one major version behind. I also updated the orchestrator to schedule the dependency audit for the first submitted GitHub project and added six unit tests covering the supported formats, version comparison behavior, missing input, empty manifests, and orchestrator integration.

**Next steps:**

I will open a draft pull request, request peer or mentor feedback, review the implementation and PR description against `CONTRIBUTING.md`, and address any feedback that improves the solution. Before marking the PR ready for review, I will rerun the targeted tests and quality checks, document the repository’s pre-existing full-suite failures, and complete Check-in 2 with the final PR link.

**Blockers:**

The repository-wide checks have pre-existing failures. Before implementation, the unit suite had 53 unrelated failures and 375 passing tests when the reproduction test was excluded. After implementation, the same 53 tests fail and 381 pass, confirming that the six new tests pass without introducing new failures. Repository-wide Ruff also reports existing errors, while Ruff, Black, and Mypy pass when run against the issue-related files.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/402

**Branch:** `feat/53-dependency-audit-tool`

**What you built:**

I added a `DependencyAuditTool` that reads dependency information from `requirements.txt`, `package.json`, and `pyproject.toml`, checks current package versions through PyPI and npm, and flags dependencies that are more than one major version behind. The tool can receive manifest contents directly or retrieve supported root-level files from GitHub, and the agent orchestrator now schedules the audit for the first submitted GitHub project.

**Tests added or updated:**

I updated `tests/unit/test_dependency_audit_tool.py` with six tests covering Python dependency auditing, npm dependency auditing, standard and Poetry `pyproject.toml` dependencies, empty manifests, missing input, and orchestrator plan integration. All six new tests pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

The repository contains documented pre-existing failures. Before implementation, the unit suite had 53 unrelated failures and 375 passing tests when the reproduction test was excluded. After implementation, the same 53 tests fail and 381 tests pass, confirming that the contribution introduced six passing tests and no new failures. Repository-wide Ruff also contains pre-existing errors, while targeted Ruff, Black, Mypy, and unit tests pass for all issue-related files.

**Draft PR feedback received from:** none 


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer or maintainer feedback was received. Reviewer feedback was not provided as part of the Summer 2026 course workflow, so I reviewed the pull request myself, confirmed that the issue-specific tests and quality checks passed, and documented the repository's unrelated pre-existing failures.

**How you responded:**

No code-review response or additional code change was required. I kept the pull request available for maintainers, verified that the branch contained the completed implementation and documentation, and finished the contribution reflection.

---

### Reflection

**What was harder than you expected?**

The hardest part was defining the correct scope for a feature that did not already exist. Issue #53 sounded like a single new agent tool, but the tool needed actual dependency-file contents while the existing `TechDetector` only received file paths and the existing `GitHubTool` mainly returned repository metadata. I had to trace the agent flow before deciding that the new tool should support both direct manifest contents and GitHub repository input. Handling dependency formats was also more complex than expected because version declarations can contain ranges, environment markers, Git URLs, workspace references, aliases, and unpinned packages. Another challenge was separating failures caused by my work from the repository's existing failures. I recorded a baseline, compared the full unit-suite results before and after implementation, and used targeted Ruff, Black, Mypy, and pytest commands to prove that my files were clean.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase requires more restraint than building a project from scratch. In my own project, I might redesign the data flow immediately, but in PathReview I needed to follow the existing `BaseTool`, `ToolResult`, test, branch, and commit conventions and avoid expanding a Tier 2 issue into a larger review-pipeline refactor. I also learned to inspect not only the file named in an issue but its callers, inputs, tests, and integration points. A change can be locally correct and still be unsafe if it does not match the surrounding architecture. The baseline failures also showed me why contributors must distinguish their own regressions from existing technical debt instead of trying to fix unrelated problems inside the same pull request.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for organizing the codebase investigation, explaining unfamiliar modules, drafting a structured implementation plan, proposing edge cases, and helping interpret pytest, Ruff, Black, Mypy, Git, and pre-commit output. They also helped turn the issue requirements into concrete tests for the three supported manifest formats and the orchestrator integration. However, AI suggestions still had to be checked against the actual repository. Some early assumptions about how tools were registered or how manifest contents were already available were not confirmed until I inspected the uploaded repository files. AI also could not decide the correct scope on its own; I had to compare its suggestions with the issue body, existing interfaces, test behavior, and course requirements. The most reliable workflow was to use AI for options and explanations, then validate every decision by reading the code and running the commands locally.

**What would you do differently if you started over?**

I would record the repository-wide test, lint, and type-check baseline at the very beginning of Week 7 instead of waiting until implementation week. That would make it easier to identify pre-existing failures and avoid uncertainty when the error counts changed. I would also define the tool's input and output contract before writing the behavior tests and ask for clarification earlier about whether nested monorepo manifests were in scope. From an implementation perspective, I would consider separating manifest parsing, registry lookup, and GitHub retrieval into smaller components earlier, even if they remained in the same file, because that would make each responsibility easier to test. I would still choose issue #53, but I would open the draft pull request as soon as the first passing vertical slice was available.

**What are you most proud of from this module?**

I am most proud that I completed the full open-source contribution process rather than only writing the feature code. I claimed and scoped the issue, reproduced the missing feature, created a detailed plan, implemented the tool, integrated it with the orchestrator, added six passing tests, documented pre-existing repository failures, and opened pull request #402. The full unit suite kept the same 53 unrelated failures while the passing count increased from 375 to 381, which gave me concrete evidence that my contribution added coverage without introducing new regressions.
