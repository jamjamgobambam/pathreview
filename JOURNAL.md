## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The agent orchestrator keeps a per-user cache of session state in
`agent/memory/session_store.py`, but that cache is never invalidated when a
user requests a new review. As a result, when someone updates their portfolio
and asks for a second review, the orchestrator reuses the tool outputs computed
during the first session instead of re-running the tools against the new input.
This means users get stale, misleading feedback that ignores their latest
changes. A successful fix will ensure session state is reset (or the cached
results invalidated) at the start of each new review so tools always run
against current portfolio data.

**Branch name:** fix/43-clear-agent-session-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
