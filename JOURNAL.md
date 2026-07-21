## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In tests/unit/test_readme_scorer.py, the test_readme_with_all_quality_signals test has expectations that don't match the scorer's actual behavior. The fixture README is only 51 words long, but the test expects it to have a word count over 100 and be classified as "comprehensive", even though agent/tools/readme_scorer.py only assigns that category to READMEs with more than 500 words. Because of this mismatch, the test fails even when the scoring logic is working correctly. A successful fix would either expand the fixture so it meets the "comprehensive" threshold or update the assertions to match the category the existing fixture should receive, ensuring the test accurately validates the scorer's behavior.

**Branch name:** fix/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger