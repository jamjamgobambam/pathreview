## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The orchestrator loads cached tool results from Redis when a user requests a second review, but then ignores this loaded session state and re-executes all tools anyway. When a user updates their portfolio and requests another review within the TTL window, the system doesn't properly invalidate or check the cached results—instead it loads stale tool outputs and potentially uses them. The fix requires checking whether results already exist in the session before executing tools, ensuring that users get fresh analysis when their profile changes rather than stale results from the previous review.

**Branch name:** `fix/43-session-store-cache-invalidation`

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger