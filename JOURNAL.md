## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The agent caches tool results in Redis by profile/user ID via `session_store.py`,
and the orchestrator reloads that state on later runs. When someone updates their
portfolio and requests another review, the old session is still there, so stale
tool results can be reused instead of analyzing the new data. A successful fix
should clear (or otherwise isolate) session state at the start of each new review
so tools always re-run against the current portfolio.

**Branch name:** fix/43-stale-session-cache

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## "Is this right for me?" checklist reasoning

### Part 1 — Understanding the Issue

- [x] **I can explain the problem and expected behavior in 2–3 sentences without reading the issue.**  
  Redis session state is keyed by profile/user ID and kept across reviews. After a portfolio update, a second review can reuse old tool results. Done means each new review starts with a clean session so tools re-run on current data.

- [x] **I've located the relevant files and confirmed they exist in the codebase.**  
  Primary: `agent/memory/session_store.py`. Also involved: `agent/orchestrator.py` (loads/merges/saves session) and `agent/memory/context_manager.py` (in-memory memoization that can also leak across runs on a long-lived orchestrator). Label: `agent`.

- [x] **I can describe a concrete before-and-after.**  
  Before: user updates portfolio → requests another review → analysis still reflects prior tool results. After: same flow → tools re-execute against the updated portfolio and the review reflects new data.

### Part 2 — Tier Fit

- [x] **The tier is a realistic match for where I am right now.**  
  Tagged Tier 1 / good first issue. Scope is a localized cache/lifecycle fix in one small area of the agent system, not a multi-module feature. Good first OSS contribution: Tier 1 is the right pick.

### Part 3 — Codebase Readiness

- [x] **I've found and read the specific code the issue references.**  
  Read `SessionStore.get` / `set` / `delete`, and `Orchestrator.run` where prior session is loaded, tools run, then `session_state.update(results)` is persisted under `profile_id`.

- [x] **I've read enough surrounding context to write a rough plan for the fix.**  
  Plan: clear Redis session (and in-memory context) at the start of each review; stop merging prior-review keys into the new session; add unit tests that a second `run()` for the same profile re-executes tools.

- [x] **I've found how tests are structured for this area (or confirmed I'll add them).**  
  No dedicated `test_session_store.py` / orchestrator tests exist yet. Pattern is clear from other files under `tests/unit/` (fixtures, mocks, `@pytest.mark.unit`). Fix should include at least one new test proving a second review starts clean.

### Part 4 — Scope and Time

- [x] **I've checked issue comments / ledger claims and I'm fine with how crowded it is.**  
  Claims are non-exclusive; grade is on my own artifacts. Comfortable proceeding even if others pick the same issue.

- [x] **I've estimated the time and can finish before the Week 9 deadline.**  
  Issue lists 3–4 hours; my estimate is closer to 1–2 hours of focused work (clear session + tests), with buffer for review feedback. Fits Weeks 8–9.

- [x] **No open blockers or dependencies on other unresolved issues.**  
  Self-contained; does not require another issue to land first.

### Verdict / scope notes

All boxes checked — ready to claim and implement. Scope stays narrow: session lifecycle for a new review, not a full redesign of agent persistence (e.g. mid-review resume across restarts is a separate, larger issue). Success criteria: second review for the same user/profile does not reuse prior Redis/in-memory tool results.