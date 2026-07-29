## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In tests/unit/test_readme_scorer.py, the test_readme_with_all_quality_signals test has expectations that don't match the scorer's actual behavior. The fixture README is only 51 words long, but the test expects it to have a word count over 100 and be classified as "comprehensive", even though agent/tools/readme_scorer.py only assigns that category to READMEs with more than 500 words. Because of this mismatch, the test fails even when the scoring logic is working correctly. A successful fix would either expand the fixture so it meets the "comprehensive" threshold or update the assertions to match the category the existing fixture should receive, ensuring the test accurately validates the scorer's behavior.

**Selection reasoning:**
I chose this as a Tier 1 issue since this is my first time contributing to a codebase this size, and it let me practice navigating the repo and confirming a bug before touching anything higher-risk. The scope fit well for a first issue: it's isolated to a single test file (`tests/unit/test_readme_scorer.py`) and the scorer logic it tests (`agent/tools/readme_scorer.py`), with no Docker, database, or API dependencies involved. It also has a clear, objective pass/fail signal — running `pytest tests/unit/test_readme_scorer.py -q` — so I can verify my fix actually resolves the issue rather than just guessing.

**Branch name:** fix/156-readme-scorer-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/FremahA/pathreview/commit/cbf5072bccd021c70ee2621447e48c0b24eac642

**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` and observed that `test_readme_with_all_quality_signals` fails. The test fixture contains only 51 words, so the scorer correctly reports `word_count=51` and `word_count_category="minimal"`, causing the test's expectations of `word_count > 100` and `"comprehensive"` to fail.

**PLAN.md link:** https://github.com/FremahA/pathreview/blob/fix/156-readme-scorer-fixture-word-count/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
