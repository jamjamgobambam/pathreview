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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No comments or reviews on [PR #842](https://github.com/ascherj/pathreview/pull/842) as of this entry. I skipped the Slack peer-review pass in Week 9 (moved straight from draft to ready-for-review) rather than waiting on it, which is very likely why nothing has come in — I didn't actually ask anyone to look at it.

**How you responded:**
N/A — nothing to respond to yet. If review feedback lands after this journal is submitted, I'll address it in the PR thread directly rather than in this file, since the journal's four-week window ends here.

---

### Reflection

**What was harder than you expected?**
Reproducing the bug was harder than fixing it. The issue title says the orchestrator continues "without logging the failure," but when I actually instantiated `Orchestrator` and forced a tool to fail, it *did* log — `logger.error` fired twice, once from `_execute_tool` and once from `run()`. I almost took the title at face value and would have "fixed" something that wasn't quite the real problem. Digging further, I found the actual gap: `configure_logging()` was never called from `api/main.py`, only from a seed script, so those logs exist but aren't structured/visible the way the app intends in the real running server. That distinction — matches the letter of the issue vs. matches what's actually broken — took longer to pin down than writing the fix itself, and it's the kind of thing that's easy to skip if you're moving fast.

The other thing that ate more time than expected: environment noise that had nothing to do with the code. Port conflicts with another running instance of the same project on the same machine, a pre-commit mypy hook that behaves differently depending on which Python version happens to be on `PATH`, 182 pre-existing lint errors and 53 pre-existing failing tests in the baseline — none of that is the bug I was assigned, but all of it had to be triaged before I could trust that my own changes weren't making things worse.

**What did you learn about working in a large codebase?**
The most useful move all module was checking who actually *calls* the code before touching it. `Orchestrator` isn't wired into `core/services/review_service.py` at all — `_run_agent_orchestration` there is a placeholder stub — which I only found by grepping for callers before writing my reproduction. That single check changed my understanding of the fix's blast radius: I was free to change `tool_results`' shape because nothing in the running app depends on the old shape yet. In a codebase I own, I'd just remember that. In someone else's, the only way to know is to go look, and skipping that step would have led me to either over-engineer a backward-compatibility shim for a caller that doesn't exist, or under-estimate the risk of a real breaking change.

I also learned to distrust "this should be true" and check it. `make check` and `make test-unit` both had real, unrelated pre-existing failures — a large codebase almost never starts from a clean baseline, and "my change is correct" is a different claim from "my change is the only source of red in the output." Diffing the exact failing-test list before and after, rather than eyeballing pass/fail counts, was the only way to be sure I hadn't quietly broken something adjacent.

**How did AI tools help — and where did they fall short?**
AI assistance was strongest at speed-reading unfamiliar code and cross-referencing it: tracing `Orchestrator.run()` → `_execute_tool` → `retry_with_backoff` → back up through `review_service.py` to confirm nothing calls it yet, and doing the same for the logging-configuration gap, would have taken much longer by hand. It was also useful for triaging noise: quickly separating "182 lint errors, are any of these mine?" into a yes/no per file, and diffing failing-test lists instead of just reading counts.

Where it fell short was judgment calls that needed a human decision, not more analysis: whether to fail loud or fail soft on a total tool failure, whether to bypass a pre-commit hook when it was blocked by clearly out-of-scope pre-existing debt, and whether to mark the PR ready without real peer feedback. In each case the honest move was to surface the tradeoff and ask, not to have an AI silently pick a side — and a couple of times that meant explicitly flagging "I'm about to use `--no-verify`, here's why" rather than just doing it quietly, since a `--no-verify` commit is exactly the kind of thing that looks like corner-cutting if it isn't explained.

**What would you do differently if you started over?**
I'd actually use the Slack peer-review step instead of skipping straight to ready-for-review. It was the one part of the process I short-circuited, and the "no feedback received" entry above is a direct, honest consequence of that choice, not bad luck. I'd also record a walkthrough video in Week 8 — I marked it "not recorded" and it stayed that way, but forcing myself to narrate the reproduction out loud probably would have surfaced the logging-config discrepancy even faster, since explaining "the issue says X but I'm observing Y" out loud tends to catch that kind of mismatch.

**What are you most proud of from this module?**
Catching the `market_analyzer` unregistered-tool bug. It wasn't in the issue description at all — it turned up as a side effect while writing the reproduction script, because I registered tools deliberately incompletely to simulate a real config. It's a second, independent way to trigger the exact same silent-failure path the issue describes, which made the case for the general fix (uniform result shape + run-level status) much stronger than fixing only the one call site the issue pointed at. That's the part of this module that felt like actually understanding the system rather than just patching the reported symptom.
