## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/93

**Issue title:** Review history page displays dates in UTC instead of the user's local timezone

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The review history page is showing review timestamps as if they were in UTC instead of converting them to the visitor’s local timezone. The broken part is the frontend date formatting logic in ReviewHistoryPage.tsx and dateFormatters.ts. A successful fix would ensure the displayed review dates are adjusted to the current user’s timezone and match the actual local time the review was created.

**Branch name:** fix/93-display-dates-in-user-timezone

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger