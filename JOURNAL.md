# Module 3 Journal — PathReview

## Week 7 — Issue selection

**Issue link:** [paste GitHub issue #156 link here]

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue appears to involve a mismatch between a README scorer test fixture and the word-count assertion used by the test. The fixture text is probably shorter than the scorer expects, so the test does not accurately represent the condition it is trying to check. A successful fix would make the test fixture and assertion consistent, either by updating the fixture text or adjusting the test expectation after confirming the intended behavior. This seems scoped to the README scoring tests or related test fixtures, which makes it a manageable Tier 1 issue.

**Why this issue is a good fit:**
I chose this issue because it is labeled Tier 1 and good first issue, and it appears to be limited to the test/fixture layer rather than a large architectural change. The likely reproduction path is clear: run the relevant scorer tests, inspect the failing assertion, and compare the fixture content against the expected word-count condition. The main risk is understanding the scorer’s intended behavior before changing the test, so I will verify whether the fixture or assertion is the incorrect part before implementing a fix.

**Branch name:** fix/156-readme-scorer-word-count-fixture

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger