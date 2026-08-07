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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No code review came in. Per the course format this term, PRs don't receive
reviewer feedback — self-review against the definition-of-done stands in for it.
So there were no comments to act on; instead I re-ran my own self-review
(`make check` / `make test-unit` against the recorded baseline) before submitting.

**How you responded:**
No external changes were requested. My "response" was the self-review itself:
confirming my two files pass ruff/black/mypy individually and that I introduced
zero new failures against the documented baseline.

---

### Reflection

**What was harder than you expected?**
Getting to a clean starting point was harder than writing the feature. Before I
touched any code, the environment fought back — Docker wasn't installed, the
ChromaDB container crashed on a NumPy 2.0 incompatibility, and the seed script
choked on Windows' cp1252 console encoding. Then when I finally ran the test
suite, 53 unit tests were already failing and there were 183 lint errors on a
clean checkout, none of it mine. The real difficulty was the mental shift: my
job wasn't to fix the codebase, it was to prove I didn't make it worse. Measuring
"no new failures" against an already-broken, moving baseline was more nerve-racking
than building the tool.

**What did you learn about working in a large codebase?**
On my own projects, "done" means it works. Here, "done" meant it works *and*
matches conventions I didn't write — the `BaseTool` interface, conventional-commit
messages, Google-style docstrings, and strict mypy annotations enforced by a
pre-commit hook. I spent nearly as long reading an existing tool
(`tech_detector.py`) to copy its shape as I did writing new code. I also learned
to scope ruthlessly: I built the tool but deliberately did *not* wire it into the
orchestrator, because that code path isn't instantiated anywhere yet and touching
it would have dragged in unrelated type errors. On my own project I'd have "just
fixed everything"; in someone else's, that restraint is part of the job.

**How did AI tools help — and where did they fall short?**
AI was strongest at exploration and pattern-matching: mapping the `agent/tools`
layout quickly, drafting the manifest parsers, and scaffolding 20 tests in the
repo's existing style. Where it fell short was judgment. It couldn't decide for me
whether "more than one major behind" should mean two-or-more or one-or-more — that
is a product decision that really belongs to the maintainer. It also couldn't tell
me whether deferring the orchestrator wiring was acceptable, or reliably know the
current state of the repo without me checking. AI got me a working, well-structured
tool fast, but the calls about scope, about being transparent in the PR, and about
what "good enough" means were mine to make.

**What would you do differently if you started over?**
Two things. First, I'd start with a Tier 1 issue — I jumped to a Tier 2 as my first
contribution to an unfamiliar codebase, and a large share of my time went to
orientation rather than the feature. Second, I'd settle the orchestrator-registration
question on day one instead of building the branch, hitting the type-error wall, and
backing it out. I'd also ask the maintainer to confirm the "outdated" threshold
before coding, rather than picking a default and carrying it as an open question.

**What are you most proud of from this module?**
Not the tool itself — the discipline around it. I documented the pre-existing
failures honestly in the PR instead of pretending the suite was green, and I designed
the tool to run offline by default so its tests are deterministic and don't depend on
a live network. Choosing to be transparent about what I *didn't* do, and why, felt
more like real engineering than the code did.
