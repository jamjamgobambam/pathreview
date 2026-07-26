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

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
The issue is reproduced by running the test suite, specifically the `tests/unit/test_relevance_scorer.py` file. I accomplished this by running .venv\Scripts\pytest tests\unit\test_relevance_scorer.py and got a failure of the TestRelevanceScorer.test_query_with_partial_overlap with the following assertation failing "assert 1.0 < 0.9"

**PLAN.md link:** [link to PLAN.md in your fork]

**Blockers or open questions:**
No Blockers
