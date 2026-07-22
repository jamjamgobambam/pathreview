## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
When a user runs a portfolio review more than once, PathReview reuses cached agent
session data keyed by user ID in `agent/memory/session_store.py` instead of starting
fresh. That means tool results from an earlier review can stick around after the user
updates their portfolio, so the orchestrator may skip re-running tools and return
stale analysis. A successful fix should clear or invalidate that session state between
reviews so each run reflects the latest portfolio data.

**Selection notes ("Is this right for me?"):**
- Tier 1 / good first issue with a clear bug description and a small relevant file list
  (`session_store.py`), estimated at 3–4 hours.
- Scope feels manageable for a first contribution to a large codebase: focused on
  session lifecycle / cache invalidation rather than a broad feature rewrite.
- I can reproduce the bug locally once the app is running, and the fix should be
  testable with unit tests around session clear/delete behavior.
- Tradeoff: many classmates have also claimed this issue, so I’ll coordinate via the
  issue thread and focus on a clean, well-tested fix rather than racing a PR.

**Branch name:** fix/43-session-state-not-cleared

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
