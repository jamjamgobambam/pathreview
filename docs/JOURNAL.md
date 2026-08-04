## Week 7 — Issue selection

**Issue link:** (https://github.com/RubyM0226/pathreview)

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [*] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
test_readme_with_all_quality_signals asserts data["word_count"] > 100 and word_count_category == "comprehensive", but its fixture README contains only 51 words, so the test fails against correct scorer behavior. I need to extend the fixture (or correct the assertion) so the test validates what it intends to.

**Reproduction commit link:** https://github.com/RubyM0226/pathreview/commit/00d77201e732d045feb3ff161cda1b9ae2b9bddb

**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` and confirmed `test_readme_with_all_quality_signals` fails with `assert 51 > 100` — the fixture README has all structural quality signals (installation,usage, badges, tech stack, demo link) but only ~51 words of prose, so it scores `word_count_category = "minimal"` instead of the `"comprehensive"` the test asserts (which requires >500 words per the
scorer's thresholds).

Steps to reproduce according to the GitHub Repo: pytest tests/unit/test_readme_scorer.py -q — observed: assert 51 > 100 fails.

**PLAN.md link:** https://github.com/RubyM0226/pathreview/blob/fix/156-README-word-count-error/PLAN.md

**Branch name:** <fix/156-README-word-count-error>

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger

**PLAN.md link:** [paste link here, e.g. https://github.com/RubyM0226/pathreview/blob/fix/156-README-word-count-error/PLAN.md]

**Blockers or open questions:**