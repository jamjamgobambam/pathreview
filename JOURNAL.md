## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157 

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The test test_query_with_partial_overlap is meant to verify that the relevance scorer correctly discounts results with incomplete keyword overlap, but its fixture data doesn't actually exercise that case. The query "Python Django web framework" is tested against a chunk that contains all four query terms, meaning the overlap is complete, not partial — so the scorer's correct output of 1.0 gets flagged as a failure against an assertion that expects a score below 0.9. This makes the test fail even though the scoring logic in the relevance scorer is behaving correctly; the bug is in the test fixture, not the implementation. A successful fix would update the chunk text (or query terms) so only some of the query terms are present, giving a genuine partial-overlap scenario that correctly validates the scorer's partial-match behavior. This affects the relevance scorer's test suite, specifically the fixtures used for keyword-overlap scoring tests.

**Branch name:** test/157-relevance-scorer-test-fixture

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger




## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
Ran `pytest tests/unit/test_relevance_scorer.py -q` and confirmed
`test_query_with_partial_overlap` fails with `assert 1.0 < 0.9`. The
scorer is behaving correctly — the fixture chunk ("Django is a Python
web framework for rapid development") contains all 4 query terms, so
full-coverage scoring of 1.0 is correct. The bug is in the test fixture,
not the scorer.

**PLAN.md link:** [link to PLAN.md in your fork]

**Blockers or open questions:**