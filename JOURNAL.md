## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bias detector in `safety/bias_detector.py` uses regular-expression patterns to identify potentially biased language in generated feedback. The existing educational-bias patterns were too narrow, so common statements about bootcamp graduates, self-taught developers, and online-course students were not consistently detected. This meant biased wording could pass through the detector even though it expressed the same assumptions as phrases the system already recognized. A successful fix would broaden the patterns while preserving the detector’s existing behavior and would include regression tests confirming that the additional phrasings are detected.

**Branch name:** `fix/bias-detector-patterns-151`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue selection notes — “Is this right for me?”

I selected a Tier 1 issue because this was my first contribution to a large, multi-module codebase and I wanted an issue with a focused and realistic scope. The change was limited mainly to `safety/bias_detector.py` and its unit tests, so I could understand the affected behavior without making architectural changes across the application. The issue matched my familiarity with Python, regular expressions, testing, and debugging. I also confirmed that the expected result could be validated with clear regression tests, which made the issue appropriate for my current skill level.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/eyobedmerhawi/pathreview/commit/b253583edc74cb4f662c6fe0f0974aa44395c1cb

**Reproduction summary:**
I reproduced the issue by testing common educational-bias statements against the detector in `safety/bias_detector.py`. Statements involving bootcamp graduates, self-taught developers, and online-course students were not consistently detected because the existing regex patterns were too narrow.

**PLAN.md link:** https://github.com/eyobedmerhawi/pathreview/blob/fix/bias-detector-patterns-151/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
The main risk is expanding the regex patterns too broadly and causing neutral statements to be flagged as biased.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I identified the root cause of the issue in `safety/bias_detector.py`, expanded the educational bias regex patterns, and added regression tests in `tests/unit/test_bias_detector.py`. I also verified the new patterns using the updated unit tests.

**Next steps:**
Run the project's quality checks, finalize the pull request, update the documentation, and submit the completed work for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/204

**Branch:**
`fix/bias-detector-patterns-151`

**What you built:**
Expanded the educational bias detection regex patterns in `safety/bias_detector.py` to recognize additional common educational bias statements. I also added regression tests to verify the new behavior while preserving the detector's existing functionality.

**Tests added or updated:**
Updated `tests/unit/test_bias_detector.py` with regression tests covering additional educational bias statements involving bootcamp graduates, self-taught developers, and online-course students.

**Self-review confirmation:**
- [x] make check passes
- [ ] make test-unit passes (repository contains pre-existing unrelated failing tests; my changes introduced no new failures. All 35 bias detector tests pass.)

**Draft PR feedback received from:**
None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided during the Summer 2026 contribution cycle. My pull request was submitted and the CI workflow was awaiting maintainer approval, but I did not receive specific code review comments that required changes.

**How you responded:**

---

### Reflection

**What was harder than you expected?**

The Git and contribution workflow was harder than I expected. The actual change to the bias detector was fairly focused, but working through branches, commits, pre-commit hooks, formatting requirements, repository links, and pull requests required much more attention than I expected. I also ran into Ruff, Black, and mypy issues while preparing the changes. Some of those problems were not directly related to the logic of my fix, so I had to learn how to separate problems caused by my changes from problems involving formatting, tooling, or the existing repository.

**What did you learn about working in a large codebase?**

I learned that making a change in a large codebase requires understanding more than just the file being edited. For Issue #151, most of my implementation involved `safety/bias_detector.py` and `tests/unit/test_bias_detector.py`, but I still needed to understand the project's testing, formatting, type-checking, Git, and contribution conventions. I also learned not to modify unrelated files just because automated tools change them. Compared with my own projects, contributing to someone else's code requires being much more careful about limiting the scope of a change and following the standards that already exist.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for helping me understand unfamiliar errors, reason about the regex patterns, troubleshoot Git commands, and interpret output from Ruff, Black, mypy, and pytest. AI also helped me break the issue into smaller steps instead of trying to understand the entire repository at once. However, I learned that I could not blindly follow every suggested command or change. At different points I still needed to inspect the actual repository, terminal output, Git status, and assignment requirements myself. For example, repository and branch links had to be verified against my actual fork rather than assumed. AI was most effective as a guide, but I still had to verify that its suggestions matched the real state of the project.

**What would you do differently if you started over?**

I would read the assignment templates and `CONTRIBUTING.md` more carefully before making my first commit. I initially focused mostly on solving the technical issue, but later learned that the journal format, correct branch URL, commit structure, and contribution process were also important parts of the assignment. I would also check `git status` more frequently and make smaller commits so unrelated formatting changes could be identified immediately. That would have made the process cleaner and saved time later.

**What are you most proud of from this module?**

I am most proud that I worked through a real open-source contribution workflow instead of only getting the code to work locally. I expanded the educational bias detection patterns, added regression tests, got all 35 bias detector tests passing, worked through the project's formatting and type-checking requirements, and submitted the change as a pull request. More importantly, I now have a much better understanding of how to move from identifying an issue to planning, implementing, testing, documenting, and submitting a contribution for review.
