# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/54

**Issue title:** Add a plan validation step that checks tool prerequisites before executing the plan

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The agent orchestrator (`agent/orchestrator.py`) builds a flat, linear execution plan
and runs each analysis tool in a fixed order without ever checking whether a tool's
prerequisites actually ran and produced usable output. As a result, dependent tools
receive empty or hardcoded inputs — for example `market_analyzer` is always handed
`{"detected_skills": {}}`, so it never sees the skills that `skill_extractor` produced,
and `skill_extractor` assumes GitHub repo metadata that may never have been fetched.
A successful fix introduces an explicit tool dependency graph (a DAG) in a new
`agent/tools/tool_dependencies.py` and a validation step in the orchestrator that,
before execution, confirms each tool's upstream dependencies were satisfied — failing
fast (or skipping with a clear, logged reason) instead of silently running tools on
missing data. This makes the agent's plan correct-by-construction and its failures
diagnosable, which is the core of reliable multi-tool agent orchestration.

**Branch name:** feat/54-plan-dag-validation

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this right for me?" reasoning

- **Tier acknowledgement:** This is a **Tier 3** issue (labels: `tier-3`, `agent`,
  `enhancement`, `devops`). I chose Tier 3 on purpose because my goal for this module
  is to practice real AI-engineer *agent architecture* work — planning, dependency
  resolution, and plan validation — rather than a one-line bug fix.
- **Scope fit:** The change is tightly bounded to the `agent/` subsystem. It is one
  new module (`tool_dependencies.py`) plus a validation hook in `orchestrator.py`.
  The five tools are small (~100–160 lines each) and already expose clear
  input/output contracts via the `ToolResult` dataclass, so the dependency edges are
  discoverable from the code (e.g. `market_analyzer` consumes `detected_skills`,
  `skill_extractor` consumes `repo_metadata`). The 8–12h effort estimate fits the
  Weeks 8–9 window.
- **Why not a lower tier:** The Tier-1/2 agent items are smaller reliability tweaks
  (e.g. exponential backoff). This issue is the most representative of agent-design
  work and gives me a concrete DAG/planning artifact to talk about in the Week 10
  reflection.
- **Risk noted:** It is a popular issue (a few cohort members have also commented to
  claim it). Cohort issues are graded per-student on our own forks and are not
  required to be merged upstream, so working in parallel is acceptable; I will still
  record it on the ledger for visibility.

**Setup verification (Week 7):**
- `.env` created from `.env.example` (`LLM_PROVIDER=mock`, no API key needed).
- `docker compose up -d` — Postgres (5433) and Redis (6379) healthy.
- `make setup` completed: `.venv` (Python 3.11), dependencies installed, Alembic
  migrations applied, database seeded (test users `user1..3@example.com`), frontend
  deps installed.
- `make run` — frontend confirmed loading at http://localhost:5173, API at :8000.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/MollyMoriJing/pathreview/commit/8ff7d2d2dc82fe60a1032dc866de94c336afb283

**Reproduction summary:**
Running `scripts/repro_issue_54.py` (real tools, no network/Redis/LLM), `skill_extractor`
detects 11 skills but `market_analyzer` returns `in_demand_skills=[]` and
`market_alignment_score=0.0` while the run still reports success — confirming the
orchestrator executes a dependent tool on empty input with no prerequisite check.

**PLAN.md link:** https://github.com/MollyMoriJing/pathreview/blob/feat/54-plan-dag-validation/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
- Scope: the issue asks for *validation*, but the visible symptom is caused by missing
  *data propagation* in `_build_plan` (`agent/orchestrator.py:130`). Will confirm with the
  maintainer whether the PR should also wire upstream outputs downstream (planned as a
  separate commit).
- The repo already fails `make typecheck` (~103 pre-existing mypy errors), so `make check`
  is red independent of my change; my new files will be kept mypy-clean and I'll note the
  baseline in the PR.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core of the fix (PLAN.md sub-tasks 1–4):
- Added `agent/tools/tool_dependencies.py` — `TOOL_DEPENDENCIES` DAG, `validate_plan()`
  (cycle + ordering), `find_cycle()`, `unmet_prerequisites()`, `PlanValidationError`.
- Wired validation into `Orchestrator.run()` (raises `PlanValidationError` on a
  mis-ordered/cyclic plan) and added run-time prerequisite gating (skips a tool whose
  prerequisites failed, with a recorded reason).
- Added `_resolve_inputs()` so upstream outputs flow downstream. Re-running
  `scripts/repro_issue_54.py` now shows `market_analyzer.market_alignment_score` at
  ~0.68 (was 0.0).

**Next steps:**
Finish/expand unit tests (sub-task 5), re-run `make check` + `make test-unit` against the
recorded baseline to confirm no new failures, open a draft PR for peer feedback, and fill
in the PR template.

**Blockers:**
- Open scope question for the maintainer: validation only, or also the data propagation
  that fixes the empty market analysis? (Included both, kept `_resolve_inputs` separable.)
- `make check` / `make test-unit` have large pre-existing failures (53 failing tests, 103
  mypy errors) unrelated to this issue; tracking a before/after baseline to prove my change
  adds none.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/760

**Branch:** `feat/54-plan-dag-validation`

**What you built:**
Made the agent orchestrator dependency-aware. Added a `TOOL_DEPENDENCIES` DAG and
`validate_plan()` that rejects mis-ordered or cyclic plans before execution, run-time
gating that skips any tool whose prerequisites failed (with a recorded reason), and
`_resolve_inputs()` that feeds each tool's upstream outputs into it — so `market_analyzer`
now scores real skills (`market_alignment_score` ~0.68) instead of returning an all-zero
result on empty input.

**Tests added or updated:**
- `tests/unit/test_tool_dependencies.py` — valid / mis-ordered / empty plans, cycle
  detection, and `unmet_prerequisites` gating (missing vs. failed prerequisites).
- `tests/unit/test_orchestrator.py` — `market_analyzer` scores non-zero once skills
  propagate; a dependent is skipped when its prerequisite fails (and never executed); an
  invalid plan raises `PlanValidationError` before any tool runs.
- 15 tests total, all passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(Per the module's pre-existing-failures guidance, "passes" = my change introduces no new
failures. Documented baseline: `make test-unit` 53 failed/375 passed → 53 failed/390 passed
(identical failing set + my 15 new tests); `make typecheck` 103 mypy errors → 103. The new
files are fully ruff/black/mypy clean.)_

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback arrived. Reviewer feedback is not a feature in the
Summer 2026 cohort, and as of submission PR #760 had 0 comments and 0 reviews. If a
maintainer responds later, I'll engage with it and document the exchange here.

**How you responded:**
_(N/A — no feedback to respond to.)_

---

### Reflection

**What was harder than you expected?**
I expected the hard part to be writing the DAG validator; it was actually working around
the repo's own broken baseline. On a clean clone, `make test-unit` already had 53 failing
tests and `make typecheck` reported 103 mypy errors, so "run `make check` before your PR"
was meaningless as a pass/fail gate. I had to stop and record an explicit before/after
baseline (53 failing → still 53 failing + my 15 new passing tests) just to *prove* my change
introduced no regressions. Untangling the stated issue from the real one was also harder than
expected: issue #54 asked for "plan validation," but the visible bug — `market_analyzer`
returning all zeros — was actually caused by `_build_plan` passing a hardcoded
`{"detected_skills": {}}`, i.e. missing data propagation, not missing validation.

**What did you learn about working in a large codebase?**
Contributing to someone else's code is mostly *reading and tracing*, not writing. The bug
surfaced in `agent/tools/market_analyzer.py` but its root cause was two files away in
`agent/orchestrator.py`, and I only found it by following the data (skills detected →
never passed on → zeroed result). I also learned the discipline of scope restraint: the
codebase had 103 pre-existing type errors, but the right move was to leave them alone and
keep my diff surgical rather than "fix everything," even though the pre-commit hook kept
tripping on that debt and forced me to commit some changes with `--no-verify`. In my own
projects I'd have just reformatted the whole file; here that would have buried the actual
change under noise for a reviewer.

**How did AI tools help — and where did they fall short?**
AI was strongest at fan-out reading — quickly mapping how the five tools' inputs and outputs
connect, which is what let me define the `market_analyzer → {skill_extractor, tech_detector}`
dependency edges — and at generating the validator, the reproduction script, and unit tests
that matched the repo's existing `@pytest.mark.unit` style. Where it fell short was judgment:
the *decisions* were mine to make. AI couldn't tell me whether shipping the data-propagation
fix alongside the validator was in-scope for the issue, or whether to model
`skill_extractor → github_tool` as a hard prerequisite (I decided against it, because
`skill_extractor` works on a resume alone and enforcing that edge would break resume-only
analyses). Those trade-offs needed a human call, and I documented them in the PR's "Notes for
Reviewers" rather than letting a tool decide silently.

**What would you do differently if you started over?**
I'd check the repo's baseline health *before* choosing an issue — knowing up front that
`make check` was already red would have shaped my whole testing strategy earlier. I'd also
weigh crowding more heavily: #54 already had four other students claim it, and picking a
less-contested issue might have made peer review more useful. And I'd open the PR as a draft
mid-week instead of finishing everything first, so there was a real window for feedback
before the deadline.

**What are you most proud of from this module?**
The reproduction script (`scripts/repro_issue_54.py`). It turns an abstract "the orchestrator
doesn't check dependencies" complaint into a one-command demo: before my fix it prints
`market_alignment_score = 0.0` while `skill_extractor` clearly found 11 skills, and after the
fix the same script prints `0.68` with 9 in-demand skills. Being able to show the bug and the
fix that concretely — and to prove zero regressions against a messy baseline — is the part of
this contribution I'd actually want to point a reviewer (or an interviewer) at.
