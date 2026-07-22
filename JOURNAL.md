## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/75

**Issue title:** Add integration tests for the full safety middleware chain

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Unit tests exist for the individual `safety/` components (prompt defense, content
filter, bias detector, PII scrubber), but no test runs a request through the
full safety stack in the order listed in the issue
(prompt defense → content filter → bias detector → PII scrubber). The
`tests/integration/` directory currently has only an `__init__.py`, so the
`test_safety_middleware.py` module requested by the issue does not exist yet.
A successful fix adds that integration test module with fixtures covering pass
and fail cases for each layer. (Estimated effort per the issue: 4–7 hours.)

**Branch name:** feat/75-safety-middleware-integration-tests

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Selection reason** I have software development experience and have contributed to open source projects in the past, so I think this issue has the right difficulty for me.
