## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The `/health` API endpoint currently reports the status of the application's dependencies, but its safety event metric is not connected to the actual safety monitoring system. The `safety_events_last_hour` field currently returns a placeholder value of zero, so operators cannot use the health endpoint to see recent safety activity. This issue affects `api/routes/health.py` and `safety/monitoring.py`. A successful fix would connect the health check to the safety monitoring data and return an accurate count of safety events from the last hour.

**Is this right for me? — Selection reasoning:**
I selected this issue because it is a Tier 1 issue with a limited and clearly defined scope. The relevant code is mainly contained in two Python files, and the existing `SafetyMonitor` class already provides event-counting functionality that I can investigate and extend. The issue will give me experience working with an existing FastAPI endpoint, Redis-based monitoring, and automated testing without requiring major architectural changes. Based on the stated scope and estimated effort, I believe I can complete and test the change within the Module 3 timeline.

**Branch name:** fix/68-safety-event-count-health-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[Paste the GitHub link to the reproduction commit here\]](https://github.com/bing-ying-li/pathreview/blob/fix/68-safety-event-count-health-check/REPRODUCTION.md)

**Reproduction summary:**
I reproduced the issue by reviewing the pre-fix version of `api/routes/health.py`. The `safety_events_last_hour` field was initialized to `0` and was never updated using recent safety event data from Redis, causing the health endpoint to always report zero events.

**PLAN.md link:** [\[Paste the GitHub link to PLAN.md here\]](https://github.com/bing-ying-li/pathreview/blob/fix/68-safety-event-count-health-check/PLAN.md)

**Walkthrough video (recommended):**

<img src ="issue-68-reproduction.gif" width="500">

**Blockers or open questions:**
The repository currently has several unrelated failing unit tests. Testing for this issue will focus on `tests/unit/test_health.py` and `tests/unit/test_safety_monitoring.py`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the main solution for Issue #68. The health-check endpoint now includes a `safety_events_last_hour` field, which reports the number of safety events recorded during the previous hour. I used the existing `SafetyMonitor` functionality and kept the current PostgreSQL, Redis, vector database, and timestamp information in the health-check response.

I also added a unit test in `tests/unit/test_health.py` to confirm that the health-check endpoint returns the correct recent safety-event count.

**Next steps:**
I will finish testing the health-check and safety-monitoring functionality, run the complete unit test suite, review the changes against the project contribution standards, and update the draft pull request. I will also request feedback before marking the pull request as ready for review.

**Blockers:**
GNU Make is not available in my Windows PowerShell environment, so I am running the equivalent Python and testing commands directly through the project virtual environment. The complete unit test suite also contains several failures in modules unrelated to Issue #68, which need to be compared with `upstream/main` to confirm that they are pre-existing.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/210

**Branch:** `fix/68-safety-event-count-health-check`

**What you built:**
I updated the health-check endpoint to include the number of safety events recorded during the previous hour. The endpoint creates a `SafetyMonitor` using the existing Redis connection and calls `get_recent_event_count(window_hours=1)` to obtain the value. The existing database, Redis, vector database, and timestamp health information remains available in the response.

**Tests added or updated:**
I added `tests/unit/test_health.py`, which verifies that the health-check response includes the `safety_events_last_hour` field and returns the value provided by `SafetyMonitor`.

I also ran `tests/unit/test_safety_monitoring.py`, which verifies that:

- Safety events are recorded correctly.
- Recent safety events are counted correctly.
- Redis errors return a safe value of zero instead of breaking the monitoring functionality.

The Issue #68 related test results were:

- `tests/unit/test_health.py`: 1 passed
- `tests/unit/test_safety_monitoring.py`: 3 passed

The complete unit test suite produced 379 passing tests and 53 failures. The failures occurred in unrelated areas such as keyword searching, PII scrubbing, README parsing, resume parsing, review services, skill extraction, and technology detection. These failures are being compared with `upstream/main` to confirm that this contribution did not introduce new failures.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** The complete unit test suite produced 379 passing tests and 53 pre-existing
failures. Running the same test suite against upstream/main confirmed that
the failures were not introduced by this contribution.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided for Summer 2026. My pull request is still available for review, but I did not receive any maintainer comments that required changes.

**How you responded:**
No changes were required because no reviewer feedback was provided.

---

### Reflection

**What was harder than you expected?**
The hardest part was understanding an existing codebase before making a small change. My issue sounded simple at first: add the number of recent safety events to the health-check response. However, I had to understand how the existing health check worked, where the safety monitoring logic was located, and how the different services such as PostgreSQL and Redis were already being checked. I also had to make sure my change fit the existing structure instead of adding unrelated logic. Another challenge was working with the development environment and tests because some existing tests were already failing for reasons unrelated to my issue, so I had to separate problems caused by my code from problems already in the repository.

**What did you learn about working in a large codebase?**
I learned that contributing to a large codebase is very different from building my own project. In my own project, I usually know where everything is and can change the structure whenever I want. In PathReview, I first had to understand the project's existing conventions and dependencies. Even a small change can affect other parts of the application, so it is important to keep the implementation focused and avoid unnecessary modifications. I also learned the importance of using a separate feature branch, checking the upstream repository, reviewing the diff before committing, and keeping the commit history related to the issue.

**How did AI tools help — and where did they fall short?**
AI tools were most helpful when I needed to understand unfamiliar code, interpret error messages, work through Git commands, and decide how to test my changes. They also helped me understand the purpose of parts of the health-check code and suggested ways to structure the implementation. However, AI could not fully understand the repository without me checking the actual files and running the code. Some suggestions had to be adjusted to match the real project structure. I still needed to run the tests, inspect Git output, check the branch and upstream repository, and verify that the final implementation actually worked in PathReview.

**What would you do differently if you started over?**
If I started again, I would spend more time exploring the repository and running the existing test suite before changing any code. This would give me a clearer baseline of which tests were already failing and make debugging easier later. I would also review the issue requirements and trace the relevant functions before beginning implementation instead of making changes while I was still learning how the project worked. I would keep my branch and commits more focused from the beginning so that the final pull request contained only changes directly related to the issue.

**What are you most proud of from this module?**
I am most proud that I was able to contribute to an unfamiliar existing project instead of only working on a project that I created myself. I worked through the repository setup, Git branching and upstream workflow, implementation, testing, documentation, and pull-request process. By the end of the module, I had a much better understanding of what an actual open-source contribution workflow looks like and felt more confident navigating a larger codebase.
