# JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

The agent currently stores its state only in memory while it is processing a review. If the API server restarts, the running review loses its progress and has to start over. This issue affects the agent orchestration and state management components, where the workflow state is not persisted. A successful fix will save the agent's progress so long-running reviews can continue after a restart instead of starting over.

**Issue selection reasoning:**

I reviewed the issue scope and confirmed that the affected area is mainly the agent orchestration and state management code. The issue is larger than a small bug because it may require persistence, restart recovery, and tests, but the expected behavior is clearly described. I am comfortable working with Python backend code and Redis, and I can divide the work into smaller steps such as understanding the current state flow, adding persistence, and testing recovery after a restart. Although it is a Tier 3 issue, I believe it is challenging but realistic within the Module 3 timeline.

**Branch name:** fix/47-agent-state-persistence

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/GargiBhise/pathreview/commit/c17a60d

**Reproduction summary:**

I ran the application locally and traced the complete review workflow. By inspecting the orchestrator and session store, I found that session state is loaded before execution but saved only after all tools complete. This means intermediate progress may be lost if the API restarts before the final save.

**PLAN.md link:**
https://github.com/GargiBhise/pathreview/blob/fix/47-agent-state-persistence/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**
No blockers. The implementation was completed and submitted as PR #834.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

- Investigated the orchestrator flow and identified where session state is loaded and persisted.
- Implemented checkpoint-based session persistence after each successful tool execution.
- Verified that previously completed tool results can be restored from the session store.

**Next steps:**

- Add unit tests for checkpointing and resume behavior.
- Run validation checks.
- Open the pull request and update documentation.

**Blockers:**

The repository contains pre-existing mypy errors and unrelated failing unit tests that are outside the scope of this issue.

---

### Check-in 2 (end of week)

**PR link:**

https://github.com/ascherj/pathreview/pull/834

**Branch:**

`fix/47-agent-state-persistence`

**What you built:**

Implemented incremental session checkpointing so completed tool results are saved after each successful tool execution. When the API restarts, the orchestrator restores the saved session state and skips tools that have already completed, allowing the workflow to resume instead of restarting from the beginning.

**Tests added or updated:**

Created `tests/unit/test_orchestrator.py` covering:

- checkpoint persistence after successful tool execution
- restoring completed tools from session state
- execution without a session store

**Self-review confirmation:**

- [x] Focused orchestrator unit tests pass
- [x] Ruff checks pass
- [x] Python syntax validation passes

The repository contains pre-existing unrelated mypy errors and failing unit tests that were not introduced by this PR.

**Draft PR feedback received from:**

None



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer or maintainer feedback was received before the end of the module. My pull request remains open for future review.

**How you responded:**

N/A

---

### Reflection

**What was harder than you expected?**

I expected writing the code to be the hardest part, but it wasn't. The hardest part was understanding a codebase that someone else had written. At first, I couldn't even tell where the review process started or how the orchestrator, session store, and different tools were connected. I spent a lot more time reading code and tracing the execution flow than actually writing my solution. Once I understood the flow, the implementation itself felt much more manageable.

**What did you learn about working in a large codebase?**

When I work on my own projects, I already know why every file exists because I created it. Here, I had to understand other people's design decisions before making any changes. I learned that it's important not to jump into coding immediately. Spending time reading the existing code, looking at related modules, and understanding how everything fits together saves a lot of time later and reduces the chances of breaking something unintentionally.

**How did AI tools help — and where did they fall short?**

AI helped me understand unfamiliar code much faster. It was useful for explaining classes, suggesting where to look next, and helping me think through different implementation ideas. But it couldn't tell me the correct solution just by looking at the issue. I still had to verify everything against the actual codebase, understand why the bug existed, and decide whether a suggested change really fit the existing architecture.

**What would you do differently if you started over?**

I would spend the first day just exploring the codebase instead of trying to solve the issue immediately. I also think I chose a fairly challenging Tier 3 issue for my first open source contribution. Even though I managed to complete it, I underestimated how much time it would take just to understand the existing system. Next time, I would plan more time for reading and debugging before writing any code.

**What are you most proud of from this module?**

I'm most proud that I didn't give up when the project felt overwhelming at the beginning. There were times when I was confused about how everything connected, but by breaking the problem into smaller pieces, I was able to understand the workflow, implement the fix, write tests, and submit a real pull request. That gave me much more confidence about contributing to codebases that I didn't build myself.