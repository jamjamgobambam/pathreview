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

## Week 8 — Implementation

*To be filled in Week 8.*
