## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156
**Issue title:** README scorer test fixture is too short for its own word-count assertion
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue affects the unit tests for the README scoring module in `tests/unit/test_readme_scorer.py`. The `test_readme_with_all_quality_signals` test asserts that a README fixture has a word count greater than 100, but the current test fixture string only contains ~51 words, causing `pytest` to fail. A successful fix will expand the mock README text in the fixture to over 100 words so that the word-count assertion passes as intended.

**Branch name:** fix/156-readme-scorer-fixture-length
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Paste your commit link here after pushing]
**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` on branch `fix/156-readme-scorer-fixture-length`. Confirmed `test_readme_with_all_quality_signals` fails with `AssertionError: assert 51 > 100` because the string fixture in `test_readme_scorer.py` has only 51 words.

**PLAN.md link:** [Paste link to PLAN.md in your GitHub fork]
**Walkthrough video (recommended):** 
**Blockers or open questions:**
None.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
- Located `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py`.
- Identified that the test fixture string had only ~51 words, causing `assert data["word_count"] > 100` and `assert data["word_count_category"] == "comprehensive"` to fail.
- Expanded the inline `readme` string fixture to exceed 500 words while maintaining all quality signals (badges, code blocks, links, lists, tech stack section).

**Next steps:**
- Run local linting and testing checks via `make check` and `make test-unit`.
- Open a Pull Request on GitHub and request peer review.
- Fill out Check-in 2 and submit the working branch URL to the course portal.

**Blockers:**
None.

---

### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/817
**Branch:** fix/156-readme-scorer-fixture-length
**What you built:**
Expanded the mock README fixture string inside `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` to >500 words. This resolves the failing `word_count` and `word_count_category` assertions without changing any underlying scoring algorithm logic in `agent/tools/readme_scorer.py`.

**Tests added or updated:**
- `tests/unit/test_readme_scorer.py`: Expanded the `readme` text string fixture inside `test_readme_with_all_quality_signals`. The updated test covers the scenario where a README containing all quality signals (badges, installation, usage, demo links, tech stack) also meets the word count threshold required to qualify for the `"comprehensive"` word count category.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
N/A haven't requested a review
**How you responded:**


---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] Check-in 2 complete — awaiting review

**Summary of feedback:**
N/A — Review has not been requested yet.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Navigating a codebase with hundreds of files and identifying the exact scope of my issue was more challenging than I anticipated. Additionally, figuring out how to fix the fixture so that all related test cases passed required careful trace-backs.

**What did you learn about working in a large codebase?**
- **Read the documentation first:** Thoroughly reading the project's documentation and contribution guidelines provides critical context for understanding what the project expects.
- **Plan before coding:** Mapping out a solution beforehand prevents wasted effort and keeps the scope manageable.
- **Test thoroughly:** Writing, running, and documenting test cases is essential to ensure changes work as intended without breaking existing behavior.

**How did AI tools help — and where did they fall short?**
Claude was particularly useful during the implementation phase. It helped construct the expanded text fixture accurately, handling precise whitespace and line-count requirements that initially caused test failures.

However, AI tools fell short in several areas:
- **Planning & Edge Cases:** Gemini helped during the initial planning phase, but its suggested solutions failed to pass all test cases. Iterating with it didn't resolve the issues, requiring manual adjustments alongside Claude.
- **Git Safety:** Claude attempted to create Git commits automatically without explicit authorization when instructed only to edit files, forcing me to run `git revert`.
- **Bypassing Checks:** When tests failed in the CI environment, Claude suggested committing with `--no-verify` to bypass pre-commit hooks, which I had to explicitly reject to maintain project standards.

**What would you do differently if you started over?**
I would dedicate more time to the initial planning phase to thoroughly understand the root cause before writing any code. While AI is a helpful assistant, I would avoid relying on it blindly, ensuring that I manually validate every change rather than accepting temporary fixes.

**What are you most proud of from this module?**
I am proud of successfully navigating a large, unfamiliar codebase to fix a real bug and submit a Pull Request. I am also proud of learning how to use AI tools responsibly—recognizing their limitations, managing their output, and taking ownership of the final codebase quality.