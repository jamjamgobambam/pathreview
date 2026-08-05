## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Selection notes:**
I selected issue #47 as a Tier 3 issue because I wanted to push past a beginner-level fix and take on a challenging problem like agent state persistence across restarts. This problem touches concurrency, idempotency, and system reliability, which are skills I want to build.

**Problem summary:**
When the agent processes a review, its progress lives only in memory: `agent/orchestrator.py` runs through a plan of tool calls (GitHub analysis, tech detection, README scoring, skill extraction, etc.), and `agent/memory/context_manager.py` caches each tool's output as it goes, but none of this is written to Redis until the entire plan finishes. If the API server restarts partway through, everything completed up to that point is discarded, since there's no partial state saved anywhere durable. A successful fix would save the orchestrator's progress to Redis after each tool step completes rather than only at the end, and on restart, check that saved state to skip steps already done instead of re-running them, while making sure a crash mid-save can't leave the stored state half-written or inconsistent.

**Branch name:** fix/47-agent-state-not-persisted-on-restart

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/krishan-g/pathreview/commit/e04cbe7

**Reproduction summary:**
I wrote `scripts/repro_issue47.py` / `scripts/repro_issue47_worker.py`, which run `Orchestrator.run()` directly against real local Redis over a fixed 3-tool plan, hard-killing the process (`os._exit`) partway through to simulate an API restart. I observed that after the crash Redis has nothing saved for the profile even though one tool had already completed, and that re-running afterward re-executes every tool from scratch instead of resuming.

**PLAN.md link:** https://github.com/krishan-g/pathreview/blob/fix/47-agent-state-not-persisted-on-restart/PLAN.md

**Walkthrough video (recommended):** Not recorded yet.

**Blockers or open questions:**
`Orchestrator` currently has no callers anywhere in the live app — `core/services/review_service.py` uses a hardcoded placeholder instead of calling into `agent/orchestrator.py`. I'm not yet sure whether wiring `Orchestrator` into the real review pipeline is part of this issue's scope or a separate follow-up; I want to raise this with a mentor before Week 9.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are implemented in `agent/orchestrator.py` and `agent/memory/session_store.py`. `Orchestrator.run()` now checkpoints each tool's result to Redis right after that tool finishes (keyed by tool name plus a hash of its input), instead of only writing once at the very end. On a resumed run, any step whose key is already in the checkpointed state gets skipped instead of re-executed. `SessionStore.set()` now returns True or False instead of silently swallowing write failures, and the orchestrator logs clearly if a checkpoint write fails. I also added two test files, `tests/unit/test_orchestrator_checkpointing.py` and `tests/unit/test_session_store.py`, covering per-step checkpoint timing, resume-skip behavior, input-hash differentiation, and checkpoint failure visibility.

**Next steps:**
I ran `make check` and `make test-unit` and compared results against a clean baseline of the unmodified code to confirm nothing new broke. Next I need to write the PR description (documenting the pre-existing failures I found, per the instructions), open a draft PR, and share it in Slack for peer or mentor feedback.

**Blockers:**
`make typecheck`'s full command (`mypy api/ core/ ingestion/ rag/ agent/ safety/`) currently cannot complete on my machine. It crashes almost immediately because a numpy stub file uses Python 3.12+ syntax that conflicts with the project's mypy config (`python_version = "3.11"`), combined with my venv running Python 3.14 (pyenv's pinned 3.11.9 has a broken system library on my machine and I did not want to modify system libraries to fix it). I confirmed this crash also happens on the unmodified codebase, so it is pre-existing and unrelated to my change. To still verify my work, I scoped mypy to `agent/` directly (which does not touch numpy) and confirmed the same pre-existing errors exist before and after my change, with no new ones added (see Check-in 2 for the exact count used by the actual pre-commit gate).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/877

**Branch:** `fix/47-agent-state-not-persisted-on-restart`

**What you built:**
I changed `Orchestrator.run()` to checkpoint each tool's result to Redis immediately after that tool succeeds, instead of writing the entire session state once at the end of the plan. A resumed run now checks each step against the checkpointed state (keyed by tool name and input hash) and skips anything already completed, so an API restart mid-review no longer loses finished work or forces a full re-run.

**Tests added or updated:**
`tests/unit/test_orchestrator_checkpointing.py` (5 tests: per-step checkpoint timing, resume skips completed steps, different input is not treated as already done, checkpoint write failures are logged, and an interrupted-then-resumed run matches an uninterrupted run) and `tests/unit/test_session_store.py` (4 tests covering the new True/False return value on `SessionStore.set()`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Note on what "passes" means here: this codebase has documented pre-existing failures (182 pre-existing ruff errors, 52 files needing black formatting, 13 pre-existing mypy errors in `error_handling.py`, `context_manager.py`, and two `orchestrator.py` functions I did not modify, and 53 pre-existing failing unit tests, none in files I touched). I confirmed my changes introduce zero new failures in any of these categories, and my own changed and added files are fully clean under ruff, black, and mypy. `make typecheck`'s full invocation cannot complete at all due to the pre-existing numpy/Python version issue described in Check-in 1, so I verified type safety with a scoped `mypy agent/` run and the actual pre-commit mypy hook instead. One commit (`620c68b`) uses `--no-verify` because of these pre-existing errors; documented in the commit message reasoning and in the PR description.

**Draft PR feedback received from:** none.

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
No feedback has come in on PR #877. Per the course note, reviewer feedback isn't a feature for Summer 2026, so this is expected.

**How you responded:**
N/A, no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Navigating and understanding the codebase itself was the hard part, not the fix. Once I understood what was going on, the actual change was straightforward: check the tool's state after each individual tool runs instead of waiting until all tools finish, since waiting until the end is exactly what made an in-progress run vulnerable to losing everything on a crash. But getting to that understanding took real work. Figuring out how the codebase was laid out, where `SessionStore` was actually defined, what methods each object exposed, and how the pieces called into each other took longer than I expected before I could even start reasoning about the fix.

**What did you learn about working in a large codebase?**
Getting properly oriented before touching anything matters a lot more than it seems like it should. One specific moment made this real for me: while investigating in Week 8, I found that `Orchestrator` had zero callers anywhere in the live app, `core/services/review_service.py` called a hardcoded placeholder stub instead of actually invoking `agent/orchestrator.py`. If I had jumped straight into fixing `Orchestrator`'s checkpointing logic without first tracing whether it was even wired into the app, I would have missed that my fix, as scoped, doesn't yet affect any review a real user could trigger. That's the kind of thing you only catch by mapping out the codebase first instead of assuming a file named in the issue is already connected the way it looks like it should be.

**How did AI tools help, and where did they fall short?**
AI tools were most useful for tracing how `Orchestrator`, `ContextManager`, and `SessionStore` connected to each other before I could reason about where to add checkpointing, and for quickly answering "where is X defined" type questions. I wouldn't say they fell short exactly, they did what they were supposed to do. But the moment that mattered most was still something I had to do myself: actually running `scripts/repro_issue47.py` against my fixed code and reading the real output line by line to confirm `tool_a` wasn't re-executed on the simulated restart, before I trusted the fix enough to write it into the PR's manual verification steps. Asking an AI to explain the code isn't a substitute for watching the actual behavior change with my own eyes.

**What would you do differently if you started over?**
I'd spend more time in the earlier weeks actually understanding the problem and the codebase in depth, rather than doing close to the minimum required for each week's deliverable. That approach ended up pushing a lot of the real understanding to the point where I actually had to implement the fix, which made that stage harder than it needed to be. Front-loading that understanding earlier would have made the whole process smoother, even though nothing about it was especially hard in an absolute sense.

**What are you most proud of from this module?**
Opening a real pull request against a codebase that closely resembles a real-world production repository, not a toy project. Even knowing it's a simulated repo, going through the full cycle (issue selection, reproduction, planning, implementation, and a properly documented PR) gave me real confidence that I could contribute to an actual open source project.