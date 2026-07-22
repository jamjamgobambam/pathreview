## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [X] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The issue is in the README scoring unit test, where the test data is inconsistent with the expectations it sets. The fixture used by the README scorer test is too short to satisfy the assertion that the scored README should be considered “comprehensive,” so the test fails even though the scorer may be behaving correctly. A successful fix would make the fixture or the assertion match the intended test behavior, so the unit test accurately validates the README scorer’s output.

**Branch name:** fix/156-README-test-fixture-too-short

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
