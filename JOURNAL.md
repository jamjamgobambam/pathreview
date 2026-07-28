# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The agent session cache is keyed too broadly, so a later review can reuse stale tool state from an earlier review instead of starting from fresh analysis. `SessionStore` stores Redis data under a `session:{session_id}` key, but the orchestrator currently passes `profile_id` when loading and saving session state, which can make review-specific state bleed across runs for the same profile. A successful fix should use the review/session identifier for persisted agent state, prevent stale results from being reused across separate reviews, and add tests for the session persistence behavior. The affected code is primarily in `agent/memory/session_store.py` and `agent/orchestrator.py`.

**Branch name:** fix/47-persist-review-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger 

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [301da90](https://github.com/chill-one/pathreview/commit/301da9065e70814940c708327e70f1e94b56e621)

**Reproduction summary:**
Using a local in-memory Redis double, I stored state for two reviews belonging to `profile-42` through the current `SessionStore` path. Both writes produced the single `session:profile-42` key, so the second review overwrote the first and `review-1` could not retrieve its state; the focused reproduction test fails on that assertion.

**PLAN.md link:** [PLAN.md](https://github.com/chill-one/pathreview/blob/fix/47-persist-review-state/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
The agent orchestration function in `core/services/review_service.py` is currently a placeholder, so Week 9 should confirm the final review-ID propagation point. The repository also has an unrelated pre-existing mypy failure in `agent/memory/session_store.py:41`.
