# PathReview Development Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Currently, the execution state of the portfolio review agent is stored only in-memory. If the FastAPI backend server restarts or crashes while a review is in progress, all state associated with the active evaluation is lost, and the review must be restarted from scratch. A successful fix will persist the agent's state to a database or cache (such as PostgreSQL or Redis) so that in-progress review sessions can be fully restored and resumed across API restarts.

**Branch name:** fix/47-agent-state-persistence

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Is This Issue Right for Me?

#### Part 1 — Understanding the Issue
- **Can I explain what this issue is asking for in my own words?**
  - [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
  - *Reasoning/Notes:* Currently, when a user triggers a portfolio review, the agent's run state is kept strictly in-memory. If the FastAPI backend server restarts or crashes mid-review, that state is lost, leaving the review permanently in a "pending" or incomplete state with no way to recover. A successful fix will serialize and persist the agent's progress (either in PostgreSQL or Redis) so it can resume after a restart.
- **Do I understand which part of the app is affected?**
  - [x] I've located the relevant files and confirmed they exist in the codebase.
  - *Reasoning/Notes:* Affected areas include `api/routes/reviews.py` (which manages review creation and status), the database models in `core/models/` (specifically the reviews table structure), and potentially the session store in `agent/memory/session_store.py` (which uses Redis).
- **Do I understand what "done" looks like?**
  - [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
  - *Reasoning/Notes:* 
    - *Before:* If the server restarts during a review, the UI shows a stuck loading spinner or fails, and querying the API shows a lost state.
    - *After:* If the server restarts, the backend reload triggers state retrieval from database/Redis, allowing the agent to pick up where it left off, and the user eventually sees a completed review.

#### Part 2 — Tier Fit
- **Is the tier a realistic match for where I am right now?**
  - [x] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first.
  - *Reasoning/Notes:* I have prior experience with large codebases, python concurrency/async systems, and database design. Persisting complex agent state is a Tier 3 challenge that matches my technical background.

#### Part 3 — Codebase Readiness
- **Can I find the relevant code?**
  - [x] I've found and read the specific code the issue references (not just the file — the function or section).
  - *Reasoning/Notes:* Found the active endpoints in `api/routes/reviews.py`, specifically `create_review` and how it schedules the background task, and the schema definitions.
- **Do I understand the surrounding code well enough to change it safely?**
  - [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
  - *Reasoning/Notes:* Yes, the plan involves adding state-serialization capabilities to the agent orchestrator, storing this state representation in the postgres database `reviews` record or a Redis session cache on each state transition, and restoring from this persisted state upon starting the background task if it already exists.
- **Have I read the relevant test file?**
  - [x] I've found the test file for my module and read at least one test end-to-end.
  - *Reasoning/Notes:* I reviewed the tests under `tests/unit/` (specifically `test_reviews.py` or similar).

#### Part 4 — Scope and Time
- **How many others are already working on this issue?**
  - [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
  - *Reasoning/Notes:* The ledger lists 3 claims for this issue, which is standard and gives room for peer review.
- **Is the scope realistic for Weeks 8–9?**
  - [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
  - *Reasoning/Notes:* Estimated 10-15 hours of development, testing, and documentation, which is well within my availability.
- **Are there any blockers or dependencies?**
  - [x] This issue has no open blockers or dependencies on other unresolved issues.
  - *Reasoning/Notes:* No other issue blocks agent state persistence implementation.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/0773240 (Replace with actual pushed commit link)

**Reproduction summary:**
I reproduced the issue by creating a unit test with mock tools that crash midway through execution. The test confirmed that since the orchestrator only persists state at the end of the run, all results from previously successful tools were lost, requiring the entire execution to be restarted.

**PLAN.md link:** https://github.com/ascherj/pathreview/blob/fix/47-agent-state-persistence/PLAN.md (Replace with actual pushed link)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
I have no blockers. I am ready to implement the incremental state persistence during Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have implemented the fix for the orchestrator persistence bug. The `Orchestrator.run` method now saves its state incrementally to the Redis store after each tool execution, rather than only at the end. All sub-tasks from the `PLAN.md` are completed.

**Next steps:**
Submit the PR, respond to any peer review feedback, and ensure that the codebase is completely stable.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/520

**Branch:** `fix/47-agent-state-persistence`

**What you built:**
I moved the session state persistence logic inside the tool execution loop in the agent orchestrator. Now, if the FastAPI server crashes or restarts midway through a long-running review, the progress is safely stored incrementally in Redis and won't be lost.
# PathReview Development Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Currently, the execution state of the portfolio review agent is stored only in-memory. If the FastAPI backend server restarts or crashes while a review is in progress, all state associated with the active evaluation is lost, and the review must be restarted from scratch. A successful fix will persist the agent's state to a database or cache (such as PostgreSQL or Redis) so that in-progress review sessions can be fully restored and resumed across API restarts.

**Branch name:** fix/47-agent-state-persistence

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Is This Issue Right for Me?

#### Part 1 — Understanding the Issue
- **Can I explain what this issue is asking for in my own words?**
  - [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
  - *Reasoning/Notes:* Currently, when a user triggers a portfolio review, the agent's run state is kept strictly in-memory. If the FastAPI backend server restarts or crashes mid-review, that state is lost, leaving the review permanently in a "pending" or incomplete state with no way to recover. A successful fix will serialize and persist the agent's progress (either in PostgreSQL or Redis) so it can resume after a restart.
- **Do I understand which part of the app is affected?**
  - [x] I've located the relevant files and confirmed they exist in the codebase.
  - *Reasoning/Notes:* Affected areas include `api/routes/reviews.py` (which manages review creation and status), the database models in `core/models/` (specifically the reviews table structure), and potentially the session store in `agent/memory/session_store.py` (which uses Redis).
- **Do I understand what "done" looks like?**
  - [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
  - *Reasoning/Notes:* 
    - *Before:* If the server restarts during a review, the UI shows a stuck loading spinner or fails, and querying the API shows a lost state.
    - *After:* If the server restarts, the backend reload triggers state retrieval from database/Redis, allowing the agent to pick up where it left off, and the user eventually sees a completed review.

#### Part 2 — Tier Fit
- **Is the tier a realistic match for where I am right now?**
  - [x] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first.
  - *Reasoning/Notes:* I have prior experience with large codebases, python concurrency/async systems, and database design. Persisting complex agent state is a Tier 3 challenge that matches my technical background.

#### Part 3 — Codebase Readiness
- **Can I find the relevant code?**
  - [x] I've found and read the specific code the issue references (not just the file — the function or section).
  - *Reasoning/Notes:* Found the active endpoints in `api/routes/reviews.py`, specifically `create_review` and how it schedules the background task, and the schema definitions.
- **Do I understand the surrounding code well enough to change it safely?**
  - [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
  - *Reasoning/Notes:* Yes, the plan involves adding state-serialization capabilities to the agent orchestrator, storing this state representation in the postgres database `reviews` record or a Redis session cache on each state transition, and restoring from this persisted state upon starting the background task if it already exists.
- **Have I read the relevant test file?**
  - [x] I've found the test file for my module and read at least one test end-to-end.
  - *Reasoning/Notes:* I reviewed the tests under `tests/unit/` (specifically `test_reviews.py` or similar).

#### Part 4 — Scope and Time
- **How many others are already working on this issue?**
  - [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
  - *Reasoning/Notes:* The ledger lists 3 claims for this issue, which is standard and gives room for peer review.
- **Is the scope realistic for Weeks 8–9?**
  - [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
  - *Reasoning/Notes:* Estimated 10-15 hours of development, testing, and documentation, which is well within my availability.
- **Are there any blockers or dependencies?**
  - [x] This issue has no open blockers or dependencies on other unresolved issues.
  - *Reasoning/Notes:* No other issue blocks agent state persistence implementation.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/0773240 (Replace with actual pushed commit link)

**Reproduction summary:**
I reproduced the issue by creating a unit test with mock tools that crash midway through execution. The test confirmed that since the orchestrator only persists state at the end of the run, all results from previously successful tools were lost, requiring the entire execution to be restarted.

**PLAN.md link:** https://github.com/ascherj/pathreview/blob/fix/47-agent-state-persistence/PLAN.md (Replace with actual pushed link)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
I have no blockers. I am ready to implement the incremental state persistence during Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have implemented the fix for the orchestrator persistence bug. The `Orchestrator.run` method now saves its state incrementally to the Redis store after each tool execution, rather than only at the end. All sub-tasks from the `PLAN.md` are completed.

**Next steps:**
Submit the PR, respond to any peer review feedback, and ensure that the codebase is completely stable.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/520

**Branch:** `fix/47-agent-state-persistence`

**What you built:**
I moved the session state persistence logic inside the tool execution loop in the agent orchestrator. Now, if the FastAPI server crashes or restarts midway through a long-running review, the progress is safely stored incrementally in Redis and won't be lost.

**Tests added or updated:**
I updated `tests/unit/test_orchestrator_reproduction.py`. The test now asserts that the `tech_detector` tool's progress is successfully saved in the mock session store even when a subsequent tool raises a `KeyboardInterrupt` to simulate a crash.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
As per the Summer 2026 guidelines, no feedback was provided during this period. I am still awaiting review from the maintainers.

**How you responded:**
Since no feedback arrived, I did not make any further changes to the pull request. I am leaving the PR open for whenever a maintainer is able to review the state persistence logic.

---

### Reflection

**What was harder than you expected?**
Understanding the exact flow of the `agent/orchestrator.py` module and how to safely serialize the agent's intermediate state without breaking the existing in-memory execution loop. Figuring out exactly where to hook into the tool execution cycle to persist state was challenging because the control flow is quite complex. Doing this without degrading performance or introducing race conditions was more difficult than I initially anticipated.

**What did you learn about working in a large codebase?**
I learned the critical importance of reading and adhering to existing patterns rather than just writing new, isolated code. For example, I had to deeply investigate how `agent/memory/session_store.py` worked before I could start. I then had to integrate my state persistence logic cleanly using those existing interfaces instead of just hacking together a raw database connection.

**How did AI tools help — and where did they fall short?**
AI tools were fantastic for helping me understand the initial backend structure and for generating the mock test in `tests/unit/test_orchestrator_reproduction.py` to reproduce the crash. However, they fell short when trying to trace the exact state schema across multiple interconnected files. I eventually had to manually read the models and ensure the serialized state perfectly matched what the Redis store expected, as the AI hallucinated some of the schema fields.

**What would you do differently if you started over?**
I would definitely spend more time up front diagramming the execution flow of the `Orchestrator.run` method before writing any code. Having a visual model of when the tools execute and how the state mutates step-by-step would have provided a clearer roadmap. This would have made implementing the incremental persistence logic much faster and less error-prone overall.

**What are you most proud of from this module?**
I am most proud of successfully reproducing a complex, race-condition-like bug involving server restarts and state loss. Writing a rock-solid unit test that reliably crashed midway through execution proved that the issue was real and measurable. Finally, delivering a robust fix that writes to Redis after every tool execution makes the entire agent system significantly more resilient.
