# Week 7 - Issue Selection

## Selected Issue
- Issue link: https://github.com/ascherj/pathreview/issues/155
- Title: Health check references settings.redis_host, which does not exist on Settings
- Tier: tier-1

## Problem Summary Statement
The health endpoint tried to create a Redis client with settings.redis_host and settings.redis_port, but the Settings model only exposes redis_url. This causes the Redis probe to fail and incorrectly marks service health as unhealthy.

## Why This Issue Fits
- Single endpoint with clear scope
- Tier-1 starter issue
- Easy to verify with focused unit tests

## Issue Claim Artifacts
- Suggested issue comment text:

```text
Hi, I would like to work on this issue for Module 3. I can reproduce the mismatch between health check Redis settings and core Settings fields, and I will submit a fix with tests.
```

- Cohort ledger row (copy/paste):

```text
GitHub Issue: https://github.com/ascherj/pathreview/issues/155
Name: <your name>
Status: Claimed (in progress)
Repo/Fork: https://github.com/lovlynia/pathreview
```

## Fork + Setup Commit Evidence
- Fork remote: https://github.com/lovlynia/pathreview
- Branch: fix/155-health-check-settings-mismatch
- Starter commit plan:
  1. docs(module3): add week 7 issue selection and setup notes
  2. chore(module3): add week 8-10 planning and PR artifacts
