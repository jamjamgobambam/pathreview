## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The agent orchestrator persists per-user tool results in a Redis-backed session
store keyed only by user/profile ID. Because that state is never invalidated
when a new review starts, a second review for the same user replays cached tool
outputs from the earlier run instead of re-analyzing the freshly updated
portfolio. The result is that portfolio changes (new repos, updated READMEs,
added skills) are silently ignored, so the review reflects stale data. A
successful fix clears or namespaces the stored session state at the start of
each review so every review runs the tools against the current portfolio. This
mainly touches `agent/memory/session_store.py` and how the orchestrator loads
and persists session state in `agent/orchestrator.py`.

**Branch name:** fix/43-clear-session-state-between-reviews

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### "Is this right for me?" — scope reasoning

- **Scope is contained:** The fix is localized to the agent memory layer
  (`session_store.py`) and the orchestrator's load/persist logic, not spread
  across the whole codebase.
- **Effort matches estimate:** The issue is estimated at 3–4 hours, which fits a
  single focused change plus unit tests.
- **Clear success criteria:** A repeat review for the same user re-runs the
  tools rather than returning cached results — easy to assert in a test.
- **Low blast radius:** Changes are backed by existing session/context APIs and
  can be covered with unit tests without external services.
- **I understand the domain:** Caching invalidation and session lifecycle are
  well-scoped, testable concerns.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DevinChen02/pathreview/commit/d6a25b4

**Reproduction summary:**
I added `tests/unit/test_orchestrator_session_state.py`, which drives
`Orchestrator.run()` twice for the same profile using a fake Redis-backed
`SessionStore` and a tool whose output changes on every call. The second review
returns the first run's memoized result (`{"call": 1}` instead of `{"call": 2}`)
and the persisted session still holds the stale `github_tool` result — both
tests fail, confirming session/context state is never invalidated between
reviews.

**PLAN.md link:** https://github.com/DevinChen02/pathreview/blob/fix/43-clear-session-state-between-reviews/PLAN.md

**Blockers or open questions:**
Deciding between clearing the session key vs. namespacing it per review — a
review ID isn't currently threaded into `Orchestrator.run()`, so namespacing
would require a small signature change. I'll confirm nothing depends on
cross-review persistence before choosing.
