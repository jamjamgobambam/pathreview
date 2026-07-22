# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` tries to connect using
`settings.redis_host` and `settings.redis_port`, but the `Settings` config class only
defines a single `redis_url` field — those two attributes don't exist. As a result, the
Redis check always throws an `AttributeError`, and the whole health endpoint reports
"unhealthy" even when Redis is running fine. A correct fix connects using the existing
`redis_url` (e.g. via `redis.Redis.from_url()`) so the health check accurately reflects
Redis's real status. This also has zero existing test coverage, so part of the fix is
adding a test for the `/health` endpoint.

**Scope reasoning:** This is my first open-source contribution, so I chose a Tier 1 issue
per the checklist. It's isolated to one function in one file, the root cause is already
confirmed by reproducing the bug locally, and it's realistically a 1-2 hour fix plus test
writing — well within the Tier 1 time estimate. This issue already has significant activity
from other students (several claim comments and a few open PRs); per the contribution
checklist, claims are non-exclusive and my grade comes from my own artifacts, so I'm
proceeding, but will implement and write it up independently rather than referencing
anyone else's PR.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
