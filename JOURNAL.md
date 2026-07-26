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



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tanisnus/pathreview/commit/78a2f1b

**Reproduction summary:**

Wrote two failing regression tests in tests/unit/test_orchestrator_stale_cache.py and ran python -m pytest tests/unit/test_orchestrator_stale_cache.py -v — no Redis needed. Both fail as expected: a reused Orchestrator serves stale in-memory ContextManager results on the second review (github_tool ran once, not twice — the input hash is byte-identical because tool_input never includes the edited content), and a tool dropped from a later plan still lingers in the persisted session state via session_state.update(results).

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]



### Notes

- The Orchestrator isn't wired into the API yet, so this is a design-level bug in the caching logic itself.

- There are two separate caches in play, and the bug comes from how they interact.

  - Layer 1 — Redis session store (session_store.py) — keyed by user/profile ID (session:{session_id}), persists across requests, 1-hour TTL.

  - Layer 2 — In-memory ContextManager (context_manager.py) — a plain dict keyed by {tool_name}:{sha256(tool_input)}, used for within-run memoization.


### Tracing 
Trace `agent/orchestrator.py:31` for a user who just updated their portfolio:


  1. Load prior session `(orchestrator.py:47-49)`:

      session_state = self.session_store.get(profile_id) or {}
      // This pulls last run's results out of Redis by user ID.


  2. Execute the plan — each tool goes through agent/orchestrator.py:136, which checks the ContextManager first `(orchestrator.py:150-155)`:

    input_hash = ContextManager.hash_input(tool_input)
    cached_result = self.context_manager.get_tool_result(tool_name, input_hash)
    if cached_result:
        return cached_result   # <-- skips re-running the tool


  3. Persist `(orchestrator.py:65-67)`:

      session_state.update(results)
      self.session_store.set(profile_id, session_state)



### Problems


  1. The cache key ignores the portfolio data. The ContextManager key is hash(tool_input). 
  
    Look at what actually goes into tool_input in `agent/orchestrator.py:78`:

      github_tool gets {github_username, repo_name} (`orchestrator.py:94-97`) — if the user edits a project but the repo name/username is unchanged, the hash is identical → cache hit → the tool never re-runs, even though the repo content changed.

      market_analyzer gets {"detected_skills": {}} (orchestrator.py:130) — a constant.
      Its hash never changes, so after the very first run it is permanently a cache hit.

      So the cache is keyed on a proxy (repo name) rather than on the actual content being analyzed. That's the core "stale tool results instead of re-running" bug.


  2.  session_state.update(results) accumulates forever and never evicts. `(orchestrator.py:66)` It merges new results into the old dict. If the new plan contains fewer tools than before (say the user deleted the project that triggered github_tool), the old github_tool result stays in session_state and gets re-persisted to Redis indefinitely — stale data with no way to age out except the TTL.


  3. The loaded session_state is loaded but functionally dead. `(orchestrator.py:49)` It's read from Redis, but nothing in run() reads it back to decide anything — it's only written to. 
  
  So the Redis layer today doesn't serve stale results directly; it just hoards them. 
  
  The layer that actually serves stale results is the in-memory ContextManager (problem 1) if the Orchestrator instance is reused across requests — since self.context_manager is created once in `agent/orchestrator.py:29` and survives between .run() calls on a long-lived instance.

---

## Reproduction (issue #43)

Reliably reproduced via a failing regression test — no Redis required, since
the stale results are served by the in-memory `ContextManager` on a reused
`Orchestrator` instance (a long-lived service singleton).

**Steps:**

```bash
source .venv/bin/activate
python -m pytest tests/unit/test_orchestrator_stale_cache.py -v
```

**Result — both tests fail, capturing the two variants:**

1. `test_second_review_reruns_tools_after_portfolio_update` — a reused
   Orchestrator serves stale `ContextManager` results on the second review.
   The tools run once, not twice (`assert 1 == 2`). The cache key
   (`github_tool:d323f24e…`) is byte-identical across both reviews even though
   the project content changed, because `tool_input` = `{github_username,
   repo_name}` never includes the edited content (orchestrator.py:94-97).

2. `test_stale_results_not_accumulated_in_session_state` — after a review that
   drops the project from the plan, the old `github_tool` result still lingers
   in the persisted session state via `session_state.update(results)`
   (`orchestrator.py:66`).

The failing test at `tests/unit/test_orchestrator_stale_cache.py` documents the
exact location of the bug and acts as the regression guard for the fix.

