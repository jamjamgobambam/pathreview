# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/97

**Issue title:** Review progress indicator doesn't update in real time during long-running reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The review page previously showed a progress bar that reflected actual processing progress by polling `GET /reviews/{id}/status` every few seconds. This was replaced with a static spinner (`Loader` component) that spins indefinitely until the review completes, giving users no indication of how far along the analysis is. The issue lives in `frontend/src/pages/ReviewPage.tsx`, which renders only the spinner during polling, and `frontend/src/hooks/useReviewStatus.ts`, which polls the status endpoint but does not expose any progress data to the UI. A successful fix would restore a progress indicator that updates in real time as the review processes.

**Branch name:** fix/97-review-progress-indicator

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
