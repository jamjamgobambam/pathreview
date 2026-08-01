## Week 7 — Issue selection

**Issue link:** [Issue #43](https://github.com/ascherj/pathreview/issues/43)

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview stores agent session data in Redis through `agent/memory/session_store.py`, and the issue reports that the stored state can carry over when the same user requests another portfolio review. If the user updates their portfolio, stale results from the earlier review may be reused instead of every relevant tool analyzing the new information. The session store is connected to the review workflow in `agent/orchestrator.py`, so the fix will need to ensure that cached state is scoped to one review or cleared at the correct point in the workflow. A successful fix will make a second review use the updated portfolio data and will include tests proving that results from the first review do not leak into it.

**Is this right for me?:**
1. I can explain the issues in my own words
2. This is my first open source contribution. So I'm choosing Tier 1.
3. I have found and read the relevant code and test file
4. The scope is realistic, and I'm fine with others working on this as well

All boxes checked!

**Branch name:** `fix/43-clear-agent-session`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [93b87f1 - reproduce stale agent state between reviews](https://github.com/rueiliu/pathreview/commit/93b87f16ed46cd12d3c0d860f7953a7846aab711)

**Reproduction summary:**
I reproduced the issue by running two reviews for the same profile through one orchestrator with different portfolio data. The second review reused the first review's cached `market_analyzer` result, and its persisted session also retained a `readme_scorer` result that was no longer part of the updated review.

**PLAN.md link:** [Solution plan](https://github.com/rueiliu/pathreview/blob/fix/43-clear-agent-session/PLAN.md)

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I need to confirm whether one `Orchestrator` instance can serve concurrent reviews and whether Redis session state is intended to support resuming an interrupted review. The planned review-local context avoids cross-review cache races without changing that future persistence contract.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented review-local memoization in the agent orchestrator so cached tool results
cannot leak between reviews. Each review now replaces its persisted session data instead
of merging with older results, and the focused regression suite has seven passing tests
covering repeated reviews, empty plans, profile isolation, same-review memoization, and
failed reruns.

**Next steps:**
Review the final diff, run the focused tests and required repository checks again, document
the pre-existing failures, and prepare the change for peer or mentor feedback before
submitting the pull request.

**Blockers:**
The baseline repository had 182 pre-existing lint errors; after this change it has 179,
with the touched files passing Ruff and Black. The full unit suite went from 54 failures
and 31 errors to 52 failures and 31 errors because the two Issue #43 reproductions now
pass. The remaining failures are outside this issue.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/499

**Branch:** `fix/43-clear-agent-session`

**What you built:**
The orchestrator now creates a review-local memoization context and persists only the
current review's results. This prevents earlier tool output from leaking into later
reviews while preserving duplicate-call caching inside a single review.

**Tests added or updated:**
`tests/unit/test_orchestrator_session_isolation.py` covers fresh state between reviews,
replacement of persisted state, empty plans, profile isolation, same-review memoization,
and failed reruns.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(No new failures compared with the documented baseline.)

**Draft PR feedback received from:** Pending peer or mentor review
