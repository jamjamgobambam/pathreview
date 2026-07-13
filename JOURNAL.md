# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/93

**Issue title:** Review history page displays dates in UTC instead of the user's local timezone

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Review creation timestamps are stored and returned by the backend in UTC, and
the review history page renders them without converting to the viewer's local
timezone. As a result a review created at 11:00 PM EST is shown as 4:00 AM the
next day, so the listed date can be wrong for anyone not on UTC. The relevant
code lives in the frontend — `frontend/src/utils/dateFormatters.ts` (the
`formatDate`/`formatRelativeDate` helpers) and `frontend/src/pages/ReviewHistory.tsx`,
which consumes them. A successful fix parses the incoming timestamps as UTC and
formats them in the browser's local timezone so the displayed date matches what
the user actually experienced.

**Branch name:** fix/93-review-history-local-timezone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
