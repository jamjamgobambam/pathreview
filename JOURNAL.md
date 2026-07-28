## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

`test_readme_with_all_quality_signals` asserts that fixture README word count is more than 100. However the actual fixture README contains 51 words so the correct scorer behavior fails the test. Extending the fixture word count or modifying the assertion would fix this issue.

**Branch name:** fix/156-readme-scorer-test-fixture-too-short

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/thetireddude/ai201-week7-pathreview/commit/8d8dae87b67def84346d94fe3217b9eb2684d94a

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

the issue is a failing test case: `test_readme_with_all_quality_signals`. As per the issue description, running `pytest tests/unit/test_readme_scorer.py -q` reproduces the issue. It is observed that the test case fails due to an `assert data["word_count"] > 100` error.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]