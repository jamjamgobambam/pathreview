# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The README scorer has a unit test, `test_readme_with_all_quality_signals`, that
is meant to verify a rich, well-documented README gets scored as "comprehensive."
The test asserts the scorer returns `word_count > 100` and a `word_count_category`
of `"comprehensive"`, but the sample README fixture it passes in only contains
about 51 words, so the test fails (`assert 51 > 100`) even though the scorer logic
is behaving correctly. The bug is in the test fixture, not the scoring code, and
lives in `tests/unit/test_readme_scorer.py`; the scoring thresholds it depends on
are in `agent/tools/readme_scorer.py`. A successful fix extends the fixture README
so it has enough content to legitimately cross the "comprehensive" threshold —
which the scorer sets at 500+ words — so the test validates the behavior it was
written to check.

**Branch name:** test/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
