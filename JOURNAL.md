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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented `DependencyAuditTool` (`agent/tools/dependency_audit_tool.py`),
completing PLAN.md sub-tasks 1–4: parsers for `requirements.txt`, `package.json`,
and `pyproject.toml`; an injectable latest-version resolver with an optional
best-effort PyPI/npm lookup; and the major-version comparison that flags anything
more than one major behind. The Week 8 reproduction test is now a 20-case unit
suite and all 20 pass.

**Next steps:**
Self-review with `make check` / `make test-unit` against the recorded baseline,
then open a PR against the upstream repo (base `ascherj/pathreview:main`) and
self-check against the definition-of-done before marking it ready. (No peer code
review this term — self-review stands in for it.)

**Blockers:**
Resolved the two Week 8 open questions (threshold defaults to flagging 2+ majors
behind, configurable; resolver is injectable with a live fallback). New wrinkle:
registering the tool in `orchestrator.py` trips the pre-commit mypy hook on
pre-existing untyped-def errors in unrelated modules, so I deferred registration
to keep the PR scoped to #53 (documented in PLAN.md and the PR).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/899

**Branch:** feat/53-dependency-audit-tool

**What you built:**
A new `DependencyAuditTool` for the agent that reads a repo's dependency
manifests (`requirements.txt`, `package.json`, `pyproject.toml`), compares each
declared dependency against its latest release, and reports the ones trailing by
more than one major version. Latest versions come from an injected map by default
(deterministic/offline) with an optional live PyPI/npm lookup, and the flag
threshold is configurable.

**Tests added or updated:**
`tests/unit/test_dependency_audit_tool.py` — 20 unit tests covering each parser
(comments/options/extras/markers/VCS lines, dev-dependencies, non-registry specs,
PEP 621 + Poetry), version-prefix handling, name normalization, the flag
threshold and override, 0.x versions, skipping of unpinned/unknown deps, and
graceful handling of malformed manifests.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
<!-- The repo has documented pre-existing failures (53 failing unit tests, 183
ruff errors, 5 mypy errors on a clean checkout). "Passes" here means my changes
introduce ZERO new failures: after my change the suite is 53 failing / 395
passing (+20 of mine, all green), ruff is 182 (down 1), and mypy is unchanged.
My two files pass ruff/black/mypy individually. -->

**Draft PR feedback received from:** none — no code-review feedback this term; self-reviewed against the definition-of-done
