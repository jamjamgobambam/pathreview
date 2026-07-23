# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses structlog for application logging, but the shared pytest configuration does not route those events into Python's standard logging system. As a result, tests using pytest's `caplog` fixture cannot find expected messages even though those messages are emitted to stderr. The problem affects logging assertions across the test suite, including the batch processor test identified in the issue. A successful fix will adjust the test configuration so `caplog` can observe structlog events without changing production logging behavior or creating duplicate output.

**Branch name:** `fix/159-structlog-caplog-capture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Issue-fit checklist and selection notes

- [x] The issue is clearly described and labeled Tier 1.
- [x] The issue provides a precise command for reproducing the failure.
- [x] The likely implementation area is limited to shared test configuration in `tests/conftest.py`.
- [x] The expected result is measurable through existing `caplog` assertions.
- [x] The issue does not require a live LLM, external API, or architectural redesign.
- [x] The scope fits the Module 3 schedule better than the Tier 3 agent lifecycle test in issue #59.
- [x] I identified the main scope risk: a global logging change could affect unrelated tests, duplicate output, or leak state between tests.
- [ ] I reproduced the failure locally after completing setup.

I initially considered issue #59, which requests a fully stubbed end-to-end test of the agent's plan, execute, and synthesize lifecycle. I selected issue #159 instead because it offers a smaller and more measurable first contribution while still requiring me to understand PathReview's shared testing and logging conventions. This scope gives me enough time to reproduce the problem, study the existing patterns, implement a focused change, and verify that it does not disrupt other tests.
