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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. Extended the README fixture in
`test_readme_with_all_quality_signals` (`tests/unit/test_readme_scorer.py`) from
~51 words to 606 words so the scorer legitimately reports the `comprehensive`
category (500+ word threshold) instead of `minimal`. Kept every quality signal
the test asserts — installation, usage, badges, demo link, tech stack — so the
other assertions still hold. The scorer logic (`agent/tools/readme_scorer.py`)
was **not** touched; this is a test-only fix. `test_readme_scorer.py` now passes
23/23 (was 22/23). Also cleared the pre-commit `mypy` blocker by adding a
`tests.*` override in `pyproject.toml` that disables `disallow_untyped_defs` for
test modules — mirroring what `make check`'s typecheck target already does (it
excludes `tests/`), so untyped pytest functions no longer block commits.

**Next steps:**
Open a draft PR, request peer/mentor feedback in Slack, address it, then mark the
PR ready for review and fill in the template.

**Blockers:**
None. Resolved the Week 8 mypy blocker (chose the `tests.*` mypy override over
annotating ~24 unrelated test functions, to keep the bugfix diff focused).

---

### Check-in 2 (end of week)

**PR link:** <!-- TODO: paste PR URL after opening -->

**Branch:** `test/156-readme-scorer-fixture-word-count`

**What you built:**
A test-only fix for issue #156. The `test_readme_with_all_quality_signals` unit
test asserted a README scored as `comprehensive` (needs 500+ words) but fed the
scorer a ~51-word fixture, so it failed with `assert 51 > 100`. I replaced the
fixture with a genuinely comprehensive 606-word README that still exercises every
quality signal, so the test now validates the behavior it was written to check
against the scorer's real, unchanged thresholds.

**Tests added or updated:**
`tests/unit/test_readme_scorer.py` — rewrote the fixture in
`test_readme_with_all_quality_signals` and expanded its docstring to explain the
500-word `comprehensive` threshold. No assertions were weakened; the sibling
threshold tests (`minimal`/`adequate`/`comprehensive`) were left untouched.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> _Note on "passes":_ this repo has **pre-existing** failures unrelated to #156.
> Baseline before my change: `make test-unit` = 53 failed / 375 passed; `make
> check` = ruff 182 errors, mypy 103 errors (26 files). After my change:
> `make test-unit` = **52 failed / 376 passed** (only my test flipped fail→pass;
> a set-diff of the failing tests confirms **zero new failures**), and `make
> check`'s ruff/mypy counts are unchanged. Per the Week 9 guidance, "passes"
> here means my changes introduce no new failures — confirmed.

**Draft PR feedback received from:** <!-- TODO: name or Slack handle, or "none" -->

