# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The plan-execute loop in `agent/orchestrator.py` wraps every tool call in a broad `except Exception` block that swallows the error and moves on to the next step instead of surfacing it. When a tool invocation fails partway through a run, the orchestrator has no way to distinguish that failure from a normal empty result, so it produces a review with missing sections and gives the user no indication that anything went wrong. A successful fix would add proper error handling (likely tying into `agent/error_handling.py`) that logs the failure with enough context to debug it and either surfaces a partial-failure state to the user or fails the run loudly, rather than silently continuing.

**Branch name:** fix/44-orchestrator-silent-exception-handling

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/cmkhoa/codepath-pathreview/commit/099ffd91df345191b84c021c19e4b2502cd62156

**Reproduction summary:**
Wrote `tests/unit/test_orchestrator.py`, instantiating `Orchestrator` with a real tool plus a tool that always raises. Confirmed `run()` returns normally with no exception and no top-level failure signal, and that the failed tool's `tool_results` entry (`{"error": ..., "success": False}`) has a completely different shape than a successful tool's entry, with nothing distinguishing the two without inspecting keys. Also found `_build_plan()` unconditionally queues `market_analyzer` even when it isn't registered in `self.tools`, hitting the same silent-swallow path via an `Unknown tool` error.

**PLAN.md link:** https://github.com/cmkhoa/codepath-pathreview/blob/fix/44-orchestrator-silent-exception-handling/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Unsure whether the fix should make `run()` fail loud (raise) on total failure vs. always fail soft with a status field — leaning toward fail-soft, but want a mentor's take before committing to the API shape. Also need to decide whether failed tool results should still be persisted to `session_store`/`context_manager` as-is.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all of `PLAN.md`'s sub-tasks: `tool_results` entries now always have the uniform shape `{"success", "data", "error"}`; `run()` returns a top-level `"status"` (`"complete"` / `"partial"` / `"failed"`) and `"failed_tools"` list; `_build_plan()` now skips (and logs a warning for) tools not registered in `self.tools` instead of queuing them to fail with an opaque `"Unknown tool"` error; and `api/main.py` now actually calls `core.logging.configure_logging()` at startup. Rewrote `tests/unit/test_orchestrator.py` (8 tests) to cover all-success, all-fail, mixed partial failure, `TimeoutError`, no `session_store`, and the unregistered-tool skip.

**Next steps:**
Ran `make check`/`make test-unit` before and after the change and diffed the results to confirm no regressions (same 53 pre-existing failing tests byte-for-byte; lint errors went from 182 to 178, all in unrelated files). Opened the PR and worked through the self-review checklist.

**Blockers:**
None remaining — the fail-soft vs. fail-loud question from Week 8 is resolved (went with fail-soft + explicit `status` field, documented as an open discussion point for reviewers in the PR description).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/842

**Branch:** fix/44-orchestrator-silent-exception-handling

**What you built:**
Fixed `Orchestrator.run()` so a failing tool call is surfaced instead of silently swallowed: every `tool_results` entry now has a uniform `{"success", "data", "error"}` shape, and the run's return value gains a top-level `"status"` and `"failed_tools"` so callers don't have to inspect every entry to detect a failure. Also fixed `_build_plan()` queuing unregistered tools (e.g. `market_analyzer`) into that same silent-failure path, and wired up `configure_logging()` in `api/main.py`, which was never actually called at server startup.

**Tests added or updated:**
`tests/unit/test_orchestrator.py` — rewritten with 8 tests covering: a failing tool doesn't raise out of `run()`; a failed tool is reported via `failed_tools`/`status` with the same result shape as a success; all-success → `"complete"`; all-fail → `"failed"`; `TimeoutError` handled the same as other exceptions; failure reporting works with no `session_store`; an unregistered tool is skipped instead of queued to fail; and a registered-but-failing tool vs. an unregistered tool are both surfaced consistently.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both commands still surface the same pre-existing, unrelated failures documented in the PR description — 53 pre-existing failing tests, identical before/after; lint errors actually dropped from 182 to 178. No new failures were introduced by this change, and zero remaining errors touch any file this PR modifies.)

**Draft PR feedback received from:** none — moved straight to ready-for-review without a Slack peer-review pass this week.
