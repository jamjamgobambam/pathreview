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

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1012

**Branch:** feat/53-dependency-audit-tool

**What you built:**
Implemented a `DependencyAuditTool` that audits `requirements.txt`, `package.json`, and PEP 621 `pyproject.toml` dependencies and flags packages that are more than one major version behind their current PyPI or npm release. I also integrated the tool into the agent orchestrator so GitHub-backed projects automatically schedule a dependency audit.

**Tests added or updated:**
Added `tests/unit/test_dependency_audit_tool.py` to cover manifest parsing, the major-version threshold, malformed and unsupported inputs, registry failures, and mocked GitHub manifest fetching. Added `tests/unit/test_orchestrator.py` to verify dependency auditing is scheduled for GitHub-backed projects without removing the existing GitHub tool behavior. All 14 new targeted tests pass.

**Self-review confirmation:**
- [x] `make check` run — repo-wide check still reports pre-existing lint failures; this change introduced no new lint failures.
- [x] `make test-unit` run — 53 pre-existing failures remain, while passing tests increased from 375 to 389 and all 14 new tests pass.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer or reviewer feedback has arrived on PR #1012 as of Week 10. I checked the PR for submitted reviews, inline review threads, and conversation comments.

**How you responded:**


---

### Reflection

**What was harder than you expected?**

The hardest part was not writing the dependency parser itself, but understanding where the new tool belonged in an unfamiliar production codebase. I had to trace `BaseTool`, the orchestrator, existing agent tools, and the available repository data before realizing that filenames alone were not enough and that the audit needed a path to actual manifest contents.

**What did you learn about working in a large codebase?**

I learned that contributing to someone else's codebase is much more about understanding contracts and existing conventions than immediately writing code. The safest approach was to find analogous tools and tests, reproduce the missing behavior first, make a scoped plan, and compare my final results against a baseline so I could distinguish my changes from existing repository problems.

**How did AI tools help — and where did they fall short?**

AI was most useful for helping me navigate unfamiliar files, turn the issue into smaller implementation tasks, reason through version-parsing edge cases, and interpret test and lint output. It still required verification against the actual repository: for example, a new test initially ended up at the wrong indentation level and pytest interpreted `self` as a fixture, and AI assistance alone could not tell whether repo-wide failures were caused by my work without the baseline I had recorded.

**What would you do differently if you started over?**

I would trace the end-to-end data flow for repository contents earlier, before spending much time thinking about the parser in isolation. I would also establish the test and lint baseline immediately, run formatting before every commit attempt, and add the mocked GitHub-fetch path earlier instead of treating it as final hardening.

**What are you most proud of from this module?**

I am most proud that I took an issue in a codebase I initially understood only partially and turned it into a contribution I can actually explain from reproduction through implementation and testing. The repository still had the same 53 pre-existing unit-test failures at the end, while passing tests increased from 375 to 389, so all 14 tests added for my contribution passed without adding another repo-wide test failure.