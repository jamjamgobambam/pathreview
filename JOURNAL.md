## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've implemented the core fix. Progress against the sub-tasks in PLAN.md:

1. **Confirm instantiation** — Done. Traced where `Orchestrator`/`SessionStore` are created in the API layer. It was a useful sanity check but ended up not mattering for the fix, so no code changed here.
2. **Fix state handling in `run()`** — Done (uncommitted). In `agent/orchestrator.py` I removed the line that loaded and merged the previous session (`session_state = self.session_store.get(profile_id) or {}`), so `session_state` now starts empty and only the current review's `results` are persisted. Each review is treated as fresh.
3. **Add regression test** — In progress. The Week 8 reproduction (`tests/repro_43.py`) exists; still need to add a proper regression test in `tests/unit/test_orchestrator.py` asserting no stale keys remain after a two-review (project present → removed) scenario.
4. **Run checks** — Not started. Need to run `make test-unit` and `make check` (lint/format/typecheck).
5. **Document** — Week 8 is updated with the reproduction commit link and PLAN.md link; will update Check-in 2 once the PR is open.

**Next steps:**
- Add the regression test for the two-review scenario (step 3).
- Confirm whether `self.context_manager` also needs resetting at the start of `run()` — the plan flagged it as a possible second source of stale results.
- Run `make test-unit` and `make check`, then commit the orchestrator fix and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/798

**Branch:** `fix/43-agent-session-state-not-cleared-between-reviews`

**What you built:**
`Orchestrator.run()` used to load the previous review's session state from Redis and merge new results over it, so tool results from an earlier review (e.g. `github_tool` for a project the user later removed) lingered in the stored session. The fix treats each review as a fresh analysis: it no longer loads prior state, so only the current review's tool results are persisted and removed/changed portfolio data is no longer reflected as stale.

**Tests added or updated:**
Added `tests/unit/test_orchestrator.py` with regression coverage for issue #43. The key test (`test_removed_project_leaves_no_stale_state`) runs two reviews for the same user — one with a GitHub project, then one after the project is removed — and asserts no stale `github_tool` result survives. It was confirmed to fail before the fix and pass after. Also covers the first-review, updated-content, and no-session-store edge cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Baseline before my change: `ruff` 182 errors, `mypy agent/` 18 errors, `pytest tests/unit -m unit` 53 failed / 375 passed — all pre-existing and unrelated to this issue. After my change: no new lint, type, or test failures, and my 4 new tests pass. Per the "documented pre-existing failures" guidance, "passes" means my changes introduce no new failures.)

**Draft PR feedback received from:** pending (PR shared for review; will update with reviewer name/Slack handle)

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[Commit Link\]](https://github.com/zhannasunny/pathreview/commit/88e64c45e148a38c522007271bdf89738b70c4f9)

**Reproduction summary:**
Ran `Orchestrator.run()` twice for the same `profile_id` using an in-memory fake Redis and stub tools: review 1 with a GitHub project + README, then review 2 after removing the project. The stale `github_tool` result from review 1 was still present in the stored session after review 2, because `run()` loads the previous state and does `session_state.update(results)` instead of clearing it — confirming the bug.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Need to confirm how the API layer instantiates `Orchestrator`/`SessionStore` — whether a single `Orchestrator` (and its `ContextManager` memoization cache) is reused across reviews, which would be a second source of stale results beyond the Redis merge.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug is that the agent keeps reusing old session data for the same user instead of treating each new review as a fresh analysis. In the current flow, the session cache in session_store.py and the orchestration logic in orchestrator.py can preserve stale tool results across reviews, so updates to a user’s portfolio are not fully reflected. A successful fix would ensure that previous review state is cleared or invalidated when a new review starts, allowing the agent to rerun the relevant tools and produce up-to-date results.

**Branch name:** fix/43-agent-session-state-not-cleared-between-reviews

**Setup confirmation:** [YES] App runs locally at localhost:5173

**Cohort ledger:** [YES] Issue added to cohort ledger