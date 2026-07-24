# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
When a user submits two review requests simultaneously, both requests start the agent loop against the same profile state. The second agent loop may read stale data modified by the first, leading to inconsistent or incorrect review results. The fix adds a per-profile lock to serialize concurrent reviews so only one agent loop runs at a time for each profile.

**Scope reasoning / "Is this right for me?" checklist:**
- Single-file change (`core/services/review_service.py`) with clear entry and exit points ✓
- Issue describes a specific race condition, not vague "improve performance" scope ✓
- Fix is localized: add a lock around the existing background processing function ✓
- No new dependencies, no database schema changes, no frontend work required ✓
- Risk of scope creep is low; adjacent concerns (ingestion dedup, caching) are tracked as separate issues and intentionally left out ✓

**Branch name:** fix/82-concurrent-review-requests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/recentbontipiece/pathreview/commit/61e78c8

**Reproduction summary:**
Added two async tests in `tests/unit/test_review_service.py` that prove the race condition in issue #82: `test_process_review_serializes_same_profile_concurrency` verifies two concurrent `process_review` calls for the same profile run serially, while `test_process_review_allows_different_profiles_concurrently` verifies different profiles can still run in parallel. Without the per-profile `asyncio.Lock`, both calls would interleave and read/write shared state concurrently.

**PLAN.md link:** https://github.com/recentbontipiece/pathreview/blob/fix/82-concurrent-review-requests/PLAN.md

**Walkthrough video (recommended):** [Not recorded]

**Blockers or open questions:**
- In-process `asyncio.Lock` is sufficient for the current single-process dev server, but will silently break if the app scales to multiple workers. The review noted this; the adjacent PR for issue #32 may also touch the same locking primitive, so I may need to rebase or coordinate if that merges first.
- The shared request/background DB session gap is real but intentionally left out of scope for this PR per the reviewer's suggestion.
