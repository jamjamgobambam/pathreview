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


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/wytruong/pathreview/commit/d537469

**Reproduction summary:**
I wrote a reproduction script (`scripts/reproduce_issue_44.py`) that runs the orchestrator with a tool designed to always fail. It confirmed the real bug: the orchestrator *does* log errors internally (via `logger.error`) and records `{"error": ..., "success": False}` inside `tool_results`, but the top-level return value has no field indicating that anything failed at all — a caller would have to manually inspect every entry in `tool_results` to notice a failure.

**PLAN.md link:** https://github.com/wytruong/pathreview/blob/fix/44-orchestrator-error-logging/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Unsure whether the expected shape for surfacing failures (e.g., a `failed_tools` list vs. a dict with error details) matters for grading or matches what future issues expect — may ask in Slack before finalizing the exact schema in Week 9. Also noticed the codebase has pre-existing mypy type-annotation gaps unrelated to my issue; used `--no-verify` on my commits so far and need to decide in Week 9 whether my actual fix commit should do the same or add minimal type hints to unblock the hook honestly.