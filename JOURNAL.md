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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/umacy/pathreview/commit/REPRO_COMMIT_SHA

**Reproduction summary:**
I added a Vitest reproduction (`frontend/src/utils/__tests__/dateFormatters.test.ts`)
that pins a non-UTC timezone and feeds `formatDate` the exact offset-less UTC
string the API returns (`datetime.utcnow()` serializes with no `Z`); the tests
assert the correct local day and currently FAIL — `formatDate('2026-07-12T03:00:00')`
returns `Jul 12, 2026` when it should return `Jul 11, 2026`, confirming
`new Date()` parses the naive string as local time and shifts the calendar day.

**PLAN.md link:** https://github.com/umacy/pathreview/blob/fix/93-review-history-local-timezone/PLAN.md

**Blockers or open questions:**
Deciding whether to also fix the backend to emit timezone-aware UTC (`...Z`) or
keep the fix frontend-only; the frontend helper will be written to be idempotent
either way. Also need to confirm every date-rendering consumer routes through
these helpers so no display is missed.
