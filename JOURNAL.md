# PathReview Contribution Journal

## Week 7 - Issue Selection

**Contributor:** Sharadha Kasiviswanathan  
**GitHub username:** SharadhaK30

**Issue link:** https://github.com/ascherj/pathreview/issues/53  
**Issue title:** Implement a `DependencyAuditTool` that flags outdated major dependencies in project repos

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
I am building a new tool for the AI agent called `DependencyAuditTool`. This tool will check a project's software packages and tell the agent if any packages are outdated or need to be updated. Right now, PathReview can review project content, but it does not have a dedicated agent tool for checking dependency freshness across files like `requirements.txt`, `package.json`, and `pyproject.toml`. A successful fix would add the new tool under `agent/tools/`, connect it to `agent/orchestrator.py`, and allow the agent to include dependency update information in its overall project review.

**Branch name:** `feat/53-dependency-audit-tool`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes / checklist reasoning:**
I chose Issue #53 because it offers a good balance between learning and implementation. It is not just fixing an existing bug; it involves building a new agent tool from scratch while following the project's existing architecture. It also matches my interest in AI-powered developer tools because the feature helps the agent give more useful feedback during project reviews. The issue covers parsing different dependency file formats and checking package versions, and the estimated 5-8 hour scope makes it challenging but manageable for this milestone.

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/SharadhaK30/pathreview/commit/578d14c5f5ed4b5a2d157c7c160039057a6c1829

**Reproduction summary:**
I reproduced the feature gap by adding a unit test that expects `agent.tools.dependency_audit_tool.DependencyAuditTool` to exist for agent reviews. A direct import check currently fails with `ModuleNotFoundError`, confirming that the dependency audit tool is missing and not yet available to the orchestrator.

**PLAN.md link:** https://github.com/SharadhaK30/pathreview/blob/feat/53-dependency-audit-tool/PLAN.md

**Walkthrough video :** Loom Link attached to Notes section in Project Submission

**Blockers or open questions:**
I need to confirm the best place to source repository dependency file contents for the orchestrator. The main open design choice is whether `DependencyAuditTool` should receive file contents directly from profile data, use output from `github_tool`, or support both so unit tests can stay fast and deterministic.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the main `DependencyAuditTool` structure from `PLAN.md` in `agent/tools/dependency_audit_tool.py`. I completed parsers for `requirements.txt`, `package.json`, and `pyproject.toml`, added major-version comparison logic, and connected the orchestrator planning path so `dependency_audit` runs when supported dependency file contents are available.

**Next steps:**
I need to finish self-review, confirm the focused and repo-wide tests pass after the final cleanup, and submit the PR with the full template completed.

**Blockers:**
None. I found repo-wide lint and unit-test failures outside the dependency audit feature, then fixed them so the Week 9 self-review commands can pass locally.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/222

**Branch:** `feat/53-dependency-audit-tool`

**What you built:**
I built a new `DependencyAuditTool` that parses dependency manifests and reports packages that are more than one major version behind a supplied latest-version map. The tool returns structured findings for audited dependencies, outdated dependencies, skipped files, and warnings, and the orchestrator now adds a `dependency_audit` step when supported dependency file contents are present. I also cleaned up the pre-existing repo-wide lint and unit-test failures so the required self-review commands pass.

**Tests added or updated:**
I updated `tests/unit/test_dependency_audit_tool.py` to cover outdated dependency detection, dependencies only one major version behind, `pyproject.toml` parsing, malformed `package.json`, unsupported files, unpinned requirements, and invalid input handling. I also added `tests/unit/test_orchestrator_dependency_audit.py` to cover when the orchestrator adds or skips the dependency audit plan step.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

**Validation notes:**
Focused validation passed with `.venv/bin/pytest tests/unit/test_dependency_audit_tool.py tests/unit/test_orchestrator_dependency_audit.py -q`. Repo-wide validation now passes with `make check` and `make test-unit`; `make test-unit` reports 435 passed with one existing Pydantic deprecation warning. `make test-integration` also completes successfully by reporting that no integration test files exist to run.


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in on PR #222 during the review window (the PR shows "No reviews" and only the two expected participants). Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a sign the PR was overlooked.

**How you responded:**
N/A — no feedback arrived to respond to. I re-read the PR description and diff one more time before closing out the module, mainly to check that the "Notes for Reviewers" question I left open (whether `DependencyAuditTool` should eventually pull file contents from `github_tool` instead of profile/orchestrator input) still made sense as a flagged design decision rather than something I should have just resolved myself.

---

### Reflection

**What was harder than you expected?**
Scoping the version-comparison logic cleanly took longer than I expected. "More than one major version behind" sounds simple, but `requirements.txt`, `package.json`, and `pyproject.toml` all express versions differently (pinned exact versions, caret/tilde ranges, unpinned entries), so I had to decide how the parser should normalize each format before the major-version-gap check could even run consistently. The bigger surprise was how much of Week 9 went into fixing pre-existing repo-wide lint, mypy, and unit-test failures that had nothing to do with issue #53 — `make check` and `make test-unit` were failing on `main` before I touched anything, so I couldn't just add my feature and call it done; I had to stabilize the baseline first.

**What did you learn about working in a large codebase?**
The main lesson was that "done" in someone else's codebase includes the surrounding repo state, not just your diff. In a solo project I'd never have hit failing lint/type checks that predated my branch — I would have just fixed them as I went. Here, I had to decide how much of that cleanup belonged in this PR versus a separate one, and ultimately kept it in #222 since `make check`/`make test-unit` passing was a stated PR requirement. I also learned to design for the orchestrator's existing conventions (how `agent/orchestrator.py` decides whether to add a plan step) rather than inventing my own pattern, which meant reading several other tool integrations before writing the `dependency_audit` step.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for generating the parser boilerplate for three different manifest formats quickly and for drafting the initial test matrix (outdated dependency, one-major-version tolerance, malformed `package.json`, unsupported files, invalid input) so I wasn't starting from a blank file. It fell short on the actual design decision in the PR notes — whether `latest_versions` should be injectable versus fetched live through `github_tool`. That trade-off (test determinism vs. real-world freshness) needed my judgment about how this specific codebase's testing philosophy works, not a generic suggestion. AI also didn't catch the pre-existing repo-wide failures; I only found those by actually running `make check` and `make test-unit` myself.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` against `main` before writing any feature code, so I'd know upfront which failures were pre-existing versus introduced by my branch, instead of discovering the scope of the cleanup mid-Week-9. I'd also nail down the `latest_versions` sourcing question (profile input vs. `github_tool`) during Week 8 planning instead of leaving it as an open note for reviewers — I had enough information to make that call myself and documented it as an open question mostly out of caution.

**What are you most proud of from this module?**
I'm most proud of keeping the test suite deterministic despite the temptation to wire `DependencyAuditTool` straight into a live registry lookup. Making `latest_versions` an explicit injectable input meant the 7 focused tests (and the orchestrator planning tests) run fast and reproducibly without any network dependency, which felt like the right engineering call for a tool that other contributors will need to extend later.

