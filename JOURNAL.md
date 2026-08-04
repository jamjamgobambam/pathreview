## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Tier justification:**
This is my first open-source contribution, so per the checklist's Part 2 guidance I'm choosing Tier 1 regardless of other factors. It's also a genuine fit on scope, not just a safe default: the issue is labeled `tier-1` on the tracker itself, and my own investigation of the codebase confirms it's self-contained — the fix lives in `agent/orchestrator.py` (and possibly `agent/memory/context_manager.py`), and `Orchestrator`/`SessionStore` aren't wired into the rest of the app or called anywhere else, so fixing it doesn't require understanding how other modules (RAG, API, ingestion) interact with it. That matches the Tier 1 description exactly: a localized fix in one or two files that doesn't require whole-system understanding.

**Problem summary:**
When a user wants a new review, the previous session cache is not cleared. This means that a new review is going to take consideration of the previous session, even though it has nothing to do with it. Inside "agent/memory/session_store.py", there should be some error or missing functionality to clear the session state.

**Branch name:** fix/43-agent-session-state-error

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/nlazaro/pathreview/commit/60f71257574370eea5e00a0c4ca98c01473433da

**Reproduction summary:**
Traced the bug to `agent/orchestrator.py`. `Orchestrator.__init__` (line 29) creates a single `ContextManager` instance that lives for the lifetime of the `Orchestrator` object instead of being reset per `.run()` call, so tool results are memoized across separate reviews by `(tool_name, hash(input))`. `market_analyzer`'s input is hardcoded to `{"detected_skills": {}}` (line 130) regardless of the profile's actual data, so its hash never changes and the first review's result is silently reused for every later review — the same "stale tool results instead of re-running the tools" symptom described in the issue. `agent/memory/session_store.py` itself works correctly in isolation (`get`/`set`/`delete` are all sound); the loaded `session_state` is also merged with `.update()` rather than cleared (lines 49, 66), which could leak stale keys from a prior review into a new one.

**PLAN.md link:** https://github.com/nlazaro/pathreview/blob/fix/43-agent-session-state-error/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
The pipeline that would actually exercise this code isn't wired up yet — `core/services/review_service.py` currently returns hardcoded placeholder data instead of calling `Orchestrator`, and neither `Orchestrator(` nor `SessionStore(` is instantiated anywhere in the app or tests. So this reproduction is based on static analysis of `agent/orchestrator.py`, not an observed run through the live app. Worth confirming with the cohort lead whether fixing #43 should include adding a unit test for the orchestrator (since none exist today), and whether wiring the orchestrator into `review_service.py` is in scope or a separate ticket.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 4 sub-tasks from PLAN.md are done. `agent/memory/context_manager.py` now has a `clear()` method, called at the top of every `Orchestrator.run()` so tool results can't be memoized across separate reviews. `market_analyzer`'s input in `agent/orchestrator.py` is populated from the current run's `skill_extractor` output instead of a hardcoded empty dict. Redis-backed session state is now replaced (not merged) on every run, and the now-unnecessary load of prior session state was removed. Added `tests/unit/test_orchestrator.py` with 4 tests covering all three fixes — confirmed each one fails against the pre-fix code (by temporarily reverting in the working tree) and passes against the fix. Full baseline comparison: `make test-unit` is at 53 failed / 379 passed (same 53 pre-existing failures as before I started, plus my 4 new passing tests); ruff/black/mypy show no new errors versus the pre-existing baseline I recorded before touching any code.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md` (branch name, commit messages, docstrings), fill out and submit the PR template, and write up the pre-commit hook bypass in the PR description per the assignment's pre-existing-failures guidance.

**Blockers:**
The local `pre-commit` mypy hook fails on 14 pre-existing type-annotation errors unrelated to this change (in `agent/error_handling.py`, `agent/memory/session_store.py`, and untouched signatures in the files I edited) — it checks the full import graph, not just changed lines, so it fails on any commit touching `orchestrator.py` regardless of my change. Bypassed with `--no-verify` on both commits; will document this explicitly in the PR description.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

