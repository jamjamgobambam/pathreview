# Week 8 - Reproduction and Solution Plan

## Issue Reproduction

### Environment
- OS: macOS
- Branch: fix/155-health-check-settings-mismatch
- Service area: FastAPI health endpoint

### Reproduction Steps
1. Inspect the health route implementation in api/routes/health.py.
2. Confirm Redis probe uses settings.redis_host and settings.redis_port.
3. Inspect Settings model in core/config.py.
4. Confirm Settings exposes redis_url, not redis_host or redis_port.
5. Run endpoint logic or unit tests to observe unhealthy Redis dependency status due to settings mismatch.

### Root Cause
The route and configuration model diverged:
- Route expects host/port fields
- Config provides URL field

## Solution Plan
1. Update health route to initialize Redis from redis_url.
2. Keep behavior the same for healthy/unhealthy status semantics.
3. Add unit tests for:
   - Healthy path with all dependencies passing
   - Unhealthy path when Redis ping fails
4. Validate with targeted tests and project-level checks.

## Risks and Mitigations
- Risk: importing Redis settings at runtime can be hard to patch in tests.
  - Mitigation: patch core.config.settings and redis.Redis.from_url in tests.
- Risk: unrelated repo-wide lint/test failures may obscure issue-specific validation.
  - Mitigation: run targeted tests for the changed module and report broader baseline failures separately.

## Loom Walkthrough (<=2 min)
- Recording script prepared:
  1. Show issue and mismatch between route and Settings model.
  2. Show test failing scenario and expected behavior.
  3. Show fix strategy and updated tests.
- Loom URL placeholder: <add Loom link here>
