## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [X] Tier 1 [ ] Tier 2 [ ] Tier 3

**Issue Fit** This issue seemed to be a good fit because it matches my comfort with the codebase according to the provided checklist. I can examplin the problem and expected behavior and understand the location of which code would be changed in this branch. Since it is my first open source contribution, I chose tier 1 and can find the relevant code sections. The expectations for this issue are also reasonable to complete in this timeframe with the required changes being self-contained in a section.

**Problem summary:**
The `RelevanceScorer` in `rag/evaluator/relevance_scorer.py` scores a chunk by
the fraction of query keywords it contains, so a
chunk holding every query term correctly scores 1.0. The unit test
`test_query_with_partial_overlap` in `tests/unit/test_relevance_scorer.py` claims
to check "partial" overlap but feeds the query "Python Django web framework" into
a chunk that actually contains all four terms, then asserts the score is below 0.9.
The scorer correctly returns 1.0, so `assert 1.0 < 0.9` fails — the test is
wrong, not the code. A successful fix edits only the fixture so the chunk omits at
least one query keyword (e.g. drop "Python"), yielding a partial score that lands in the asserted 0.3–0.9 range.

**Branch name:** test/157-relevance-scorer-partial-overlap-test

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/050fc046b66dad487f3a68336c3d5cd6d6ebc6c5

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
The issue is reproduced by running the test suite, specifically the `tests/unit/test_relevance_scorer.py` file. I accomplished this by running .venv\Scripts\pytest tests\unit\test_relevance_scorer.py and got a failure of the TestRelevanceScorer.test_query_with_partial_overlap with the following assertation failing "assert 1.0 < 0.9"

**PLAN.md link:** https://github.com/AlbertMundadan/pathreview/blob/test/157-relevance-scorer-partial-overlap-test/PLAN.md

**Blockers or open questions:**
No Blockers

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I have implemented the fix to the test file by adjusting the text chunk and have run tests to ensure that all 19 tests in that file now pass. 

**Next steps:**
[What are you working on for the rest of the week?]
I need to commit these changes and draft/create the PR. I need to also review the PR conventions and requirements for contributions. 

**Blockers:**
[Anything slowing you down? Or leave blank.]
N/A

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request] https://github.com/ascherj/pathreview/pull/742

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]
test/157-relevance-scorer-partial-overlap-test 

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
In `test_query_with_partial_overlap`, the chunk `text` now omits "Python" so there is not a complete match. This now matches the expected behavior of a partial match which the test checks. 

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
I modified the "test_relevance_scorer.py" test file because this issue involved a incorrect pre-existing test. The modifciation made was to change the input text chunk so that there was actually a partial match instead of a full match. 

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
There are pre-existing issue that are outside the scope of this PR. 

**Draft PR feedback received from:** [name or Slack handle, or "none"]
"none"