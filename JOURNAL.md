## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** Tier 1

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that there is a readme scorer that is hardcoded to have the readme's word count greater than 100 words and word_count_category = "comprehensive". But our readme only has 51 words. So, I need to either increase the word count or fix the readme scorer from minimum 100 words to something like 50 so that our readme passes the test.

**Branch name:** fix/156-readme-scorer-fixture-length

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I reproduced the issue by running `pytest tests/unit/test_readme_scorer.py -q`. The test failed at `assert data["word_count"] > 100` because the fixture README only produced a word count of 51, which confirms the fixture is too short for the assertion.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]