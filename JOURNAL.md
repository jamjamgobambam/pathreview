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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I documented the pre-existing failures in the overall project
Found 182 errors with make check
53 failed, 375 passed with make test-unit

I have read through the entire test file `test_readme_scorer.py` and identified a second potential issue. While 
`assert data["word_count"] > 100` currently causes the test to fail, `assert data["word_count_category"] == "comprehensive"` is another assertion that needs to be considered. 

After fixing the README scorer test fixture to include more than 100 words, the `assert data["word_count"] > 100` part passes, but the `assert data["word_count_category"] == "comprehensive"` line causes an assertion error because the README is marked as `adequate` and not `comprehensive`. 

**Next steps:**
My next steps are to figure out how `word_count_category` is determined and edit the README to meet the `comprehensive` requirements. 

**Blockers:**
None.



---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/463)

**Branch:** fix/156-readme-scorer-fixture-word-count

**What you built:**
Expanded the README fixture in the unit test so it now exceeds the threshold for a “comprehensive” score (500+ words) and satisfies the assertions. I changed the word count assertion to match the "comprehensive" label by requiring 500+ words instead of 100. The change keeps the test focused on the original bug by updating the test input rather than changing the scorer logic.


**Tests added or updated:**
I updated the `test_readme_scorer.py` file, specifically the `test_readme_with_all_quality_signals` test. 

**Self-review confirmation:** [x] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none
