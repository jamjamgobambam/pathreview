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

## Week 8 - Reproduction & solution planning

**Reproduction commit:** https://github.com/toju-commits/pathreview/commit/821a4d876886414ccbb4f9cd17dbf480956dbd49

**Reproduction summary:**
I confirmed locally that PathReview has no `DependencyAuditTool` implementation and that `Orchestrator._build_plan()` does not schedule a dependency-audit step even when `requirements.txt` and `package.json` are present in the profile's file list. The generated plan only scheduled `tech_detector` and `market_analyzer`, with `Dependency audit scheduled: False`.

**PLAN.md:** https://github.com/toju-commits/pathreview/blob/feat/53-dependency-audit-tool/PLAN.md

**Plan commit:** https://github.com/toju-commits/pathreview/commit/d12810f857ef0bdb8c5ebdc1157e951f0781b770

**Walkthrough video:** Not recorded yet (optional)

**Blockers / open questions:**
The main open question is where the new tool should get the actual contents of `requirements.txt`, `package.json`, and `pyproject.toml`. The current agent flow exposes repository filenames to `tech_detector`, but that alone is not enough to inspect dependency versions. Before implementation, I need to trace the producer of `profile_data` and decide whether the dependency audit should receive manifest contents from an earlier layer or fetch them through the GitHub API.

## Week 9 — Implementation & PR submission

### Check-in 1 — Implementation progress

**Implementation commit:** https://github.com/toju-commits/pathreview/commit/d6615d4bc464063a8269b250256c390dedd08278

**Progress:**
Implemented `DependencyAuditTool` and integrated it into the agent orchestrator. The tool supports `requirements.txt`, `package.json`, and `pyproject.toml`, resolves current package versions through PyPI or npm, and flags dependencies that are more than one major version behind.

**Testing completed:**
Added focused unit tests for dependency parsing, version-gap behavior, malformed manifests, unsupported version specifications, registry lookup failures, and orchestrator scheduling. The targeted test suite passes with 13/13 tests.

**Repository baseline:**
Before implementation, `make test-unit` reported 375 passing and 53 failing tests. These failures were pre-existing and unrelated to Issue #53. The repository also had pre-existing repo-wide Ruff/mypy issues. My new files pass targeted Ruff, Black, and mypy checks; the commit used the existing Ruff and Black pre-commit hooks successfully, while the repo-wide mypy hook was skipped because it fails on existing unrelated agent files.

**Next steps:**
Run the final self-review, verify no new regressions compared with the baseline, review the diff for scope and maintainability, complete PR documentation, and open the pull request.