## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint
 #68

**Tier:** Tier 1

**Problem summary:**
The `/health` endpoint currently only reports basic service status (e.g.
whether the process is up and running), but it has no visibility into the
safety monitoring system's activity. Right now, if an operator wants to know
whether the safety system has flagged anything recently, they have to leave
the health check entirely and go query a separate monitoring dashboard. This
touches `api/routes/health.py` (the endpoint itself) and
`safety/monitoring.py` (where safety events are presumably already tracked
and would need to be queried by count over a time window). A successful fix
adds a `safety_events_last_hour` field to the health response so that
operators — and any automated alerting hitting `/health` — can see both
"is the service up" and "has the safety system been active" in one place,
without an extra dashboard lookup.

**Branch name:** fix/68-add-safety-count

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**