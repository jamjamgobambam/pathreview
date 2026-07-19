# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The agent session cache is keyed too broadly, so a later review can reuse stale tool state from an earlier review instead of starting from fresh analysis. `SessionStore` stores Redis data under a `session:{session_id}` key, but the orchestrator currently passes `profile_id` when loading and saving session state, which can make review-specific state bleed across runs for the same profile. A successful fix should use the review/session identifier for persisted agent state, prevent stale results from being reused across separate reviews, and add tests for the session persistence behavior. The affected code is primarily in `agent/memory/session_store.py` and `agent/orchestrator.py`.

**Branch name:** fix/47-persist-review-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger — not yet confirmed in this repository
