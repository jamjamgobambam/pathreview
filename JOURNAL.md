# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [x] Tier 2  [ ] Tier 1  [ ] Tier 3

**Problem summary:**
The orchestrator's plan-execute loop wraps every tool call in a broad `except Exception` block that silently continues on failure. When a tool call fails partway through generating a review, the orchestrator doesn't log the error or surface it to the user — it just moves on. This means users can receive an incomplete review with missing sections and no indication anything went wrong. I chose this as a Tier 2 issue because fixing it properly requires understanding how the plan-execute loop in `agent/orchestrator.py` interacts with the logging setup in `agent/error_handling.py` — it's not an isolated one-file fix, but it's also well-scoped enough (two files, a clear failure mode) that I felt comfortable taking it on given I've spent this week getting familiar with the repo. A successful fix would add proper error logging and update the loop so failures are recorded and the user is informed which sections failed, instead of failing silently.

**Branch name:** fix/44-orchestrator-error-logging

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger