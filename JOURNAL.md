## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All four sub-tasks from PLAN.md are done. The `readme` fixture in
`test_readme_with_all_quality_signals` was rewritten from ~51 words into a
genuine ~568-word README (comfortably past the 500-word `comprehensive`
threshold), preserving every quality signal the assertions check (installation
and usage sections, badges, a demo link, and a tech stack section). All
assertions were left unchanged — they now accurately describe the fixture. The
scorer itself was not touched. Change committed (`f8cf8dd`) and pushed to
`origin/fix/156-resume-scorer-test`.

**Next steps:**
Open the PR against `ascherj/pathreview` and fill out the PR template.

**Blockers:**
None specific to #156. Note: repo-wide `make check` and `make test-unit` exit
non-zero due to pre-existing failures in unrelated files (verified against the
parent commit) plus a local `black` version mismatch (project pins 24.1.0; venv
has 26.5.1). My changed lines pass ruff, the pinned black, and all 23
readme_scorer tests.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/789)

**Branch:** `fix/156-resume-scorer-test`

**What you built:**
Fixed a self-contradicting unit test: its fixture README was too short (~51
words) to satisfy its own `word_count > 100` / `word_count_category ==
"comprehensive"` assertions. Enlarged the fixture to a real ~568-word README so
both assertions hold, while keeping all quality signals intact and leaving the
scorer logic (`agent/tools/readme_scorer.py`) untouched.

**Tests added or updated:**
`tests/unit/test_readme_scorer.py` — rewrote the fixture in
`test_readme_with_all_quality_signals`; assertions unchanged. The full module
passes (23/23).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both fail repo-wide on pre-existing, unrelated issues; my changed lines are
clean — ruff clean, project-pinned black clean, 23/23 readme_scorer tests pass.)

**Draft PR feedback received from:** none

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/gulziraAbudula/pathreview/commit/cb5b62d2b9efead4b13a943a73f2382165006d7c]

**Reproduction summary:**
Ran the target test in the project venv
(`.venv/bin/python -m pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -v`);
it fails deterministically (3/3 runs) with `assert 51 > 100`. The scorer
correctly counts the ~51-word fixture as `minimal`, but the test asserts a
`comprehensive` README with `word_count > 100`, so the defect is in the test
data (`tests/unit/test_readme_scorer.py:56-57`), not the scorer.

**PLAN.md link:** [https://github.com/gulziraAbudula/pathreview/blob/fix/156-resume-scorer-test/PLAN.md]

**Walkthrough video (recommended):** [ ]

**Blockers or open questions:**
None — the plan is to enlarge the fixture to ≥ 500 words (the `comprehensive`
threshold in `readme_scorer.py:70-75`) while keeping every quality signal, so
both `word_count > 100` and `word_count_category == "comprehensive"` hold.

---

## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/156]

**Issue title:** [README scorer test fixture is too short for its own word-count assertion]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The README scorer in tests/unit/test_readme_scorer.py has a test whose fixture and assertions disagree with each other. The test test_readme_with_all_quality_signals expects a "comprehensive" README with a word count above 100, but the sample README it actually passes in only contains about 51 words. Because the scorer correctly reports that low count, the assertion word_count > 100 fails — so the test flags a problem that doesn't exist in the scoring logic itself. This affects the test suite, not the scorer implementation: the failure is a mismatch between the test data and the behavior being asserted. A successful fix makes the test internally consistent — either by enlarging the fixture README so it genuinely qualifies as comprehensive, or by adjusting the assertions to match what a ~51-word README should score — so the test passes and actually validates the intended scorer behavior.]

**Branch name:** [fix/156-resume-scorer-test]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger