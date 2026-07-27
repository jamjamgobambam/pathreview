# PLAN.md — Issue #54: DAG-based plan validation for the agent orchestrator

**Issue:** https://github.com/ascherj/pathreview/issues/54
**Title:** Add a plan validation step that checks tool prerequisites before executing the plan
**Tier:** 3 (agent, enhancement)
**Branch:** `feat/54-plan-dag-validation`

---

## 1. What needs to change

The agent **orchestrator** (`agent/orchestrator.py`) runs its analysis tools as a
flat, fixed-order list and **never checks whether a tool's prerequisites actually
ran and succeeded** before executing it. There is no model of "tool A depends on
tool B" anywhere in the `agent/` subsystem.

A correct implementation adds an explicit **tool dependency graph (a DAG)** and a
**validation step that runs before execution**:

- Structurally invalid plans (a tool whose prerequisite is missing from the plan,
  a prerequisite ordered *after* its dependent, or a cycle in the dependency config)
  are rejected **before** any tool runs, with a clear error naming the offending tool.
- At runtime, a tool whose prerequisite *ran but failed* is **skipped with a logged
  reason** instead of silently executing on missing/empty input.

This turns the agent's plan into something correct-by-construction and makes its
failures diagnosable — the core of reliable multi-tool orchestration.

## 2. Reproduction (confirmed locally, 2026-07-27)

Reproduced with `scripts/repro_issue_54.py` (real tools, no network/Redis/LLM):

```
STEP 1 — the plan the orchestrator builds
  - market_analyzer  input_keys=['detected_skills']
      >>> detected_skills passed in = {}          # hardcoded EMPTY, never populated

STEP 2 — run the plan
  skill_extractor detected 11 skills: ['AWS', 'Django', 'Docker', 'FastAPI',
      'Kubernetes', 'PostgreSQL', 'Python', 'React', 'Redis', 'SQL', 'TypeScript']
  market_analyzer.in_demand_skills       = []
  market_analyzer.market_alignment_score = 0.0     # all-zero, yet success=True
```

**Root cause:** `Orchestrator._build_plan` appends
`("market_analyzer", {"detected_skills": {}})` at `agent/orchestrator.py:127-131`
with a comment "Will be populated by context" — but it never is. Nothing validates
that `market_analyzer`'s prerequisite (`skill_extractor`) ran or that its input is
non-empty, so `market_analyzer.execute` hits its `if not detected_skills` branch
(`agent/tools/market_analyzer.py:60`) and returns a zeroed result with
`success=True`. The failure is completely silent.

## 3. Parts of the codebase involved

| File | Role in the fix |
|---|---|
| `agent/tools/tool_dependencies.py` | **NEW.** `TOOL_DEPENDENCIES` DAG, `PlanValidationError`, `validate_plan()`. |
| `agent/orchestrator.py` | Call `validate_plan()` after `_build_plan()` in `run()`; add runtime prerequisite gating in the execution loop; (decision-dependent) propagate upstream outputs in `_build_plan()`. |
| `agent/tools/base.py` | Reference only — `ToolResult(success, data, error)` is the contract used to decide if a prerequisite "succeeded". |
| `agent/tools/{skill_extractor,market_analyzer,tech_detector,github_tool}.py` | Reference only — read their `name` and input/output keys to define the dependency edges. |
| `tests/unit/test_tool_dependencies.py`, `tests/unit/test_orchestrator.py` | **NEW.** Unit tests (there are currently none for `agent/orchestrator.py`). |
| `scripts/repro_issue_54.py` | Reproduction harness; kept as a regression aid. |

## 4. Proposed dependency graph (DAG)

```
github_tool   ─┐
                ├─▶ skill_extractor ─┐
tech_detector ─┤                     ├─▶ market_analyzer
                └────────────────────┘
readme_scorer  (no dependencies)
```

`TOOL_DEPENDENCIES = {`
`  "github_tool": [], "tech_detector": [], "readme_scorer": [],`
`  "skill_extractor": ["github_tool"],           # needs repo_metadata`
`  "market_analyzer": ["skill_extractor", "tech_detector"],  # per the issue`
`}`

## 5. Actionable sub-tasks

1. **Create `agent/tools/tool_dependencies.py`** — define `TOOL_DEPENDENCIES`,
   a `PlanValidationError(Exception)`, and
   `validate_plan(plan: list[tuple[str, dict]], dependencies=TOOL_DEPENDENCIES) -> list[str]`
   that detects (a) a prerequisite missing from the plan, (b) a prerequisite ordered
   after its dependent, and (c) cycles in the config (topological sort / DFS).
2. **Wire validation into `Orchestrator.run()`** — right after `plan = self._build_plan(...)`,
   call `validate_plan(plan)`; if it returns errors, log `plan_validation_failed` and
   raise `PlanValidationError` **before** the execution loop starts.
3. **Add runtime prerequisite gating** in `run()`'s execution loop — before calling
   `_execute_tool(tool_name, ...)`, check every prerequisite's entry in `results`
   exists and is not an error/`success=False`; if a prerequisite failed, record
   `results[tool_name] = {"skipped": True, "reason": "prerequisite_failed: <name>"}`
   and `continue` instead of executing.
4. **(Decision-dependent) Propagate upstream outputs in `_build_plan()`** — replace the
   hardcoded `{"detected_skills": {}}` so `market_analyzer` receives `skill_extractor`'s
   output, and pass `github_tool`'s repo metadata into `skill_extractor`. Keep this in a
   **separate commit** from the validator (see risk #1).
5. **Add unit tests** following the existing `@pytest.mark.unit` class style:
   `test_tool_dependencies.py` (valid plan passes; missing prereq; wrong order; cycle)
   and `test_orchestrator.py` (dependent skipped when prerequisite fails; happy path
   produces a non-zero market analysis).
6. **Self-review + gate:** run `make check` (ruff/black/mypy) and `make test-unit`, add
   Google-style docstrings, and record the Week 8 progress in `JOURNAL.md`.

## 6. Inputs and outputs (what changes)

**New public API (in `tool_dependencies.py`):**
- `TOOL_DEPENDENCIES: dict[str, list[str]]` — the DAG.
- `validate_plan(plan, dependencies=TOOL_DEPENDENCIES) -> list[str]` — **in:** the
  `(tool_name, tool_input)` list from `_build_plan`; **out:** a list of human-readable
  error strings (empty = valid).
- `PlanValidationError(Exception)` — raised by the orchestrator on a structurally
  invalid plan.

**Changed behavior (in `orchestrator.py`, no signature change to `run`):**
- **In:** same `(profile_id, profile_data)`.
- **Out:** `run()` may now raise `PlanValidationError`; the returned
  `tool_results` may contain `{"skipped": True, "reason": ...}` entries for tools whose
  prerequisites failed; when data propagation (sub-task 4) lands, `market_analyzer`
  returns a real (non-zero) `market_alignment_score` for a skilled profile.

**Risks / unknowns (each tied to a concrete spot):**
- **R1 — scope boundary (biggest unknown):** the issue title asks only for
  *validation*, but the visible symptom (empty market analysis) is caused by missing
  *data propagation* in `_build_plan` (`agent/orchestrator.py:130`). Open question for
  the maintainer: should the PR fix only validation, or also the data plumbing? Plan:
  implement validation first (the requested feature), add propagation in a separate
  commit, and call this out in the PR description so it can be dropped if out of scope.
- **R2 — skip vs. raise semantics:** structural errors raise, runtime prerequisite
  failures skip. If the maintainer prefers "skip everything," the `run()` loop
  (`agent/orchestrator.py:53-62`) is the single place to change.
- **R3 — memoization interaction:** `_execute_tool` returns early on a context-cache
  hit (`agent/orchestrator.py:151-155`). The prerequisite-success check must read
  `results`, not the cache, or a cached-but-failed prerequisite could be misjudged.
- **R4 — no live call site:** `Orchestrator` is not instantiated in `api/` or `core/`
  today, so the change is exercised via `scripts/repro_issue_54.py` and new unit tests
  rather than the running app; end-to-end verification relies on those tests.

## 7. Edge cases the fix must handle

1. **Prerequisite missing from the plan:** profile has `resume_text` (→ `skill_extractor`,
   `market_analyzer`) but no `files` and no `github_username`, so `tech_detector` and
   `github_tool` are absent. `validate_plan` must flag `market_analyzer` /
   `skill_extractor` as having unmet prerequisites rather than letting them run on
   partial data.
2. **Prerequisite present but fails at runtime:** `skill_extractor` returns
   `success=False` (e.g. a resume that triggers its `except` branch). `market_analyzer`
   must be **skipped with a reason**, not executed on empty skills.
3. **Empty plan:** a profile with none of `github_username` / `files` / `readme_content`
   / `resume_text` yields `plan == []`. `validate_plan([])` must return no errors and
   `run()` must return empty results without raising.
4. **Cycle / self-dependency in the config:** if `TOOL_DEPENDENCIES` ever contains a
   cycle, `validate_plan` must detect it and raise rather than loop forever.
5. **Duplicate tool entries:** `_build_plan` can append the same tool more than once
   (the `github_tool` loop, `agent/orchestrator.py:91-100`); validation and gating must
   handle repeated `tool_name`s without false positives.

## 8. Definition of done

- `validate_plan` and the orchestrator changes are covered by unit tests; `make check`
  and `make test-unit` pass.
- Re-running `scripts/repro_issue_54.py` shows `market_analyzer` returning a non-zero,
  populated analysis (once propagation lands) **or** a clearly-logged skip — never a
  silent all-zero "success".
- PR follows `docs/CONTRIBUTING.md` (Conventional Commits, PR template) and explicitly
  states the validation-vs-propagation scope decision (R1).
