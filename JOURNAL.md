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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shriyapeddakama/pathreview/commit/54efce54c0222406b4696506ca4be508e1409fac

**Reproduction summary:**
Ran the unit suite against the project venv
(`.venv/Scripts/python.exe -m pytest tests/unit/test_readme_scorer.py -q`) and
reproduced the failure reliably: `test_readme_with_all_quality_signals` fails
with `assert 51 > 100` (`1 failed, 22 passed`). The scorer logs
`category=minimal word_count=51`, confirming the scorer is correct and the
fixture README is only ~51 words — far short of the 500 needed for the
`"comprehensive"` category the test asserts. The bug is in the test fixture, not
the scoring code.

**PLAN.md link:** https://github.com/shriyapeddakama/pathreview/blob/test/156-readme-scorer-fixture-word-count/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
The pre-commit `mypy` hook (`disallow_untyped_defs = true`, with `tests/` not
excluded) fails on the whole test file because its functions lack type
annotations. My Week 9 fix must edit this file, so I'll need to either annotate
the test functions or exclude `tests/` from mypy before the fix can be committed
with hooks active. Also want to confirm on the issue that the intended fix is to
*extend the fixture* (make it genuinely comprehensive) rather than to weaken the
assertions.
