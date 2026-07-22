## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The test `test_readme_scorer.py` fails because the test README only contains 51 words, when it needs over 100 to be "comprehensive". The issue lies with `assert data["word_count"] > 100` which expects the README to contain over 100 words. A successful fix would either a) change the assertion to lower the word count, or b) fix the README to include more words and reach the "comprehensive" level. 


**Branch name:** fix/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[link to commit documenting the reproduced issue\]](https://github.com/t1ffnyw/pathreview/commit/17dd2fcaa87e30bb2a634ff43793c099b907b59c)

**Reproduction summary:**
I reproduced the error by with the command `pytest tests/unit/test_readme_scorer.py`. The test showed that 22 cases passed and 1 failed. The failed case was an AssertionError due to the line `assert 51 > 100` inside the function `test_readme_with_all_quality_signals()`. Looking at the README used for the test, the word count of the README is 51, while the test expects it to have at least 100 words. Therefore, the assetion `assert data["word_count"] > 100` fails and the entire test fails. 

**PLAN.md link:** [link to PLAN.md in your fork](PLAN.md)

**Blockers or open questions:**
N/A