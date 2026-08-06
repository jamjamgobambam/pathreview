## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** Tier 1

**Selection Reasoning:** I chose this Tier 1 issue as a good starting point because it is focused on a small, well-scoped change and gives me a manageable way to learn how this open source project is structured. It also connects to the existing safety monitoring code, which makes it a practical first contribution for someone new to the codebase.

**Problem summary:** The /health endpoint currently reports service status, but it does not show recent safety activity. That makes it harder for operators to monitor safety events without checking a separate monitoring dashboard. A successful fix adds a safety_events_last_hour value to the health response so that information is available directly from the endpoint.

**Branch name:** feat/68-safety-event-count-health-check

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

**Reproduction commit link:** https://github.com/trihiennguye-ux/pathreview/commit/efd3b6b7dd1a56278dc7cdd725542337b796cab9

**Reproduction summary:**
- I reproduced the issue through health check endpoint and check the logs for safety_events_check_failed error. I noticed the safety_events_last_hour return 0 instead of the actual value, this is because the endpoint does not read from the Redis-backed monitoring state.

**PLAN.md link:** https://github.com/trihiennguye-ux/pathreview/blob/feat/68-safety-event-count-health-check/docs/PLAN.md

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I updated the monitoring file so that safety events are stored in a way that supports a true rolling one-hour count. I also updated the health endpoint to call the new monitoring helper and return the real count in the response payload.

**Next steps:**
I will write tests for both the monitoring logic and the health endpoint to verify the rolling-window count and confirm the endpoint field is populated correctly.

**Blockers:**
I ran into formatting errors when committing new changes and didn't fully understand the pre-commit requirements at first.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/trihiennguye-ux/pathreview/pull/1

**Branch:** feat/68-safety-event-count-health-check

**What you built:**
I rewrote the SafetyMonitor class so that it stores safety events in Redis sorted sets rather than a simple counter, which enables an accurate rolling one-hour count via ZCOUNT and includes automatic trimming of entries older than a 24-hour retention window. The health route now builds a SafetyMonitor from the existing Redis client and populates safety_events_last_hour with the real aggregate count across all event types, falling back to 0 if Redis is unavailable so the endpoint remains resilient. Unit tests were added covering both the healthy zero-event case and a case with a non-zero rolling count, using a lightweight in-memory Redis stub to avoid network dependencies.

**Tests added or updated:**
I created a new test file: tests/unit/test_health_route.py with a FakeRedis stub (sorted-set backed) covering:
- Healthy status response with zero safety events
- Correct propagation of a non-zero rolling-window event count into safety_events_last_hour

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** Still awaiting review

**Summary of feedback:**

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Getting oriented in a codebase I didn't write was much harder than I expected. As a first-time contributor, I couldn't just jump to the fix, I had to slow down and figure out how the pieces fit together before I could trust myself to change anything.

**What did you learn about working in a large codebase?**
I learned that contributing isn't just about writing code that works, it's about understanding the existing structure and conventions well enough that your change fits naturally into it. I also learned the value of paying attention to a project's tooling and process early, since small things like formatting requirements can slow you down if you skip past them.

**How did AI tools help — and where did they fall short?**
AI tools helped me ramp up faster by summarizing unfamiliar code and pointing me toward the parts most relevant to my issue, which saved a lot of time compared to reading everything cold. Where they fell short was in the actual decision-making, understanding tradeoffs and confirming a change was correct still came down to me thinking it through myself rather than taking a suggestion at face value.

**What would you do differently if you started over?**
I would spend less time trying to understand the whole codebase up front and instead focus earlier on tracing the specific path tied to my issue, digging into the root cause sooner rather than building a broad mental map first.

**What are you most proud of from this module?**
I'm most proud that I was able to take on a codebase that was completely new to me, work through the unfamiliarity, and still land a real, tested contribution. It gave me more confidence in my ability to ramp up quickly on unfamiliar systems.