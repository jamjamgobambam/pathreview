# Week 9 - PR Submission Package

## PR Metadata
- Target repo: https://github.com/ascherj/pathreview
- Fork: https://github.com/lovlynia/pathreview
- Branch: fix/155-health-check-settings-mismatch
- Primary issue: https://github.com/ascherj/pathreview/issues/155
- Related issue addressed in same file: https://github.com/ascherj/pathreview/issues/154

## Proposed PR Title
fix(api): use redis_url in health check and add dependency health tests

## PR Description Draft
### Summary
This PR fixes the health endpoint Redis configuration mismatch by constructing the Redis client from settings.redis_url instead of non-existent settings.redis_host/settings.redis_port. It also updates the PostgreSQL probe to use SQLAlchemy text() and adds focused unit tests for healthy and unhealthy dependency states.

### Issue
Closes #155
Also addresses #154 in the same endpoint.

### Changes
- Updated Redis probe initialization in api/routes/health.py to use Redis.from_url(settings.redis_url)
- Updated DB probe call to db.execute(text("SELECT 1")) for SQLAlchemy 2.x compatibility
- Added unit tests in tests/unit/test_health_route.py:
  - healthy dependencies path
  - Redis failure returns HTTP 503 with unhealthy status

### Testing Evidence
- Targeted test command:
  - .venv/bin/pytest tests/unit/test_health_route.py -v -m unit
- Required project commands run:
  - make check
  - make test-unit

### Results Summary
- Targeted health-route tests: pass (2/2)
- make check: fails due to existing unrelated baseline lint issues in other files
- make test-unit: fails due to multiple existing unrelated baseline test failures across modules

## Self-Review Checklist
- [x] Branch name follows standard format
- [x] Commit messages follow conventional commits
- [x] Fix includes test coverage for changed behavior
- [x] PR template content drafted
- [x] Risks and known baseline failures documented

## Bi-Weekly Check-ins (for grading packet)
- Check-in A: see docs/module3/week9_checkin_a.md
- Check-in B: see docs/module3/week9_checkin_b.md
