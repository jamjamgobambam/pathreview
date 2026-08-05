## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/156]

**Issue title:** [README scorer test fixture is too short for its own word-count assertion]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
I ran the test suite against the actual implementation to confirm the issue rather than guess, and found a concrete, reproducible bug: ReadmeScorer._score_readme() in agent/tools/readme_scorer.py (used by the Agent System when orchestrating a portfolio review) undercounts words for realistic README content. In the test_readme_with_all_quality_signals test case — a README with installation, usage, tech-stack, badges, and a demo link — the scorer returns a word_count of only 51, well under the 100-word threshold, so word_count_category comes back as "minimal" instead of the expected "comprehensive", even though every other quality signal (installation, usage, badges, demo, tech stack) is correctly detected. Because word_count_category and the length-based bonus in overall_score both key off this undercounted value, well-documented READMEs can be misclassified as sparse, which would push PathReview's generated feedback to unfairly flag good documentation as thin. A successful fix would correct the word-counting logic (likely how content.split() treats markdown syntax, code fences, or list markers) so word counts reflect genuine prose length, bringing test_readme_with_all_quality_signals and any other length-dependent assertions back in line with the test suite's expectations.

**Branch name:** [#156-README-scorer-test]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/AliceKindle2/pathreview/blob/fix/%23156-README-scorer-test/tests/unit/test_readme_scorer.py]

**Reproduction summary:**
Ran ReadmeScorer._score_readme() directly against the fixture in test_readme_with_all_quality_signals and found the actual word count is 51, not >100 as the test asserts — the scorer's word-splitting logic is correct, but the test fixture's markdown structure (headings, code fences, bullets, badges) inflates its apparent length without adding enough real prose to cross the threshold.

**PLAN.md link:** [https://github.com/AliceKindle2/pathreview/blob/fix/%23156-README-scorer-test/PLAN.md]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
* Still need to confirm no other test fixtures in test_readme_scorer.py (or elsewhere in the repo) share this same boundary-mismatch pattern before considering the fix complete.
* Haven't yet verified that expanded fixture text won't accidentally trip other regex-based assertions (installation/usage/tech-stack detection) once prose is added.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix identified in PLAN.md's Understand/Map steps: test_readme_with_all_quality_signals in tests/unit/test_readme_scorer.py asserted word_count > 100 and word_count_category == "comprehensive" against a fixture that only contained 51 real words once markdown syntax was stripped out. I expanded the fixture with genuine descriptive prose under each existing heading (Installation, Usage, Features, Tech Stack, Live Demo, plus a new Support section) while leaving every structural marker the other assertions depend on — badges, code fences, bullet list, demo link — untouched. I verified against the actual ReadmeScorer._score_readme() logic (no changes made to agent/tools/readme_scorer.py) that the fixture now scores 420 words on the first pass, then 500+ after adding the Support section, landing it in the "comprehensive" category as the test name intends. Ran all 23 test methods in the file against the real implementation and confirmed 23/23 pass, with no regressions to the other 22 previously-passing tests.

**Next steps:**
Scan the rest of tests/unit/ for any other fixtures asserting word-count-category boundaries to make sure this isn't a repeated pattern elsewhere. Then run the project's actual make test-unit and make check (rather than my manual harness, since pytest/structlog weren't available in my sandbox) to confirm formatting/linting/type-checking are clean, and open a draft PR for early feedback per the plan.

**Blockers:**
My local environment doesn't have network access to install pytest or structlog, so I verified correctness by exec'ing the test module directly against the real ReadmeScorer class with lightweight stand-ins for those two dependencies rather than running the project's actual make test-unit. I'm confident in the logic (23/23 assertions pass), but I still need to confirm it under the project's real test runner before treating this as done.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/AliceKindle2/pathreview/tree/fix/%23156-README-scorer-test

**Branch:** fix/#156-README-scorer-test

**What you built:**
Fixed a failing test fixture in test_readme_with_all_quality_signals (tests/unit/test_readme_scorer.py) where the sample README only contained ~51 real words despite the test asserting it should score as "comprehensive" (500+ words). Expanded the fixture with genuine descriptive prose under each existing section (Installation, Usage, Features, Tech Stack, Live Demo) plus a new Support section, while leaving agent/tools/readme_scorer.py's scoring logic untouched, since the bug was in the test data, not the implementation.

**Tests added or updated:**
Updated tests/unit/test_readme_scorer.py — specifically only the test_readme_with_all_quality_signals fixture. No other test methods in the file were changed. This test covers the ReadmeScorer tool's word-count categorization, section detection (installation/usage/tech-stack), badge detection, and demo-link detection, verifying they all still resolve correctly against the expanded fixture. Confirmed all 23 tests in the file pass against the actual ReadmeScorer implementation.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in due to no PR reviews during summer.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Environment setup ate more time than the actual code fix. Getting make test-unit and make check running on Windows required switching from PowerShell to Git Bash, installing make via Scoop, and getting Docker Desktop running before make setup would even complete. The bug itself — a test fixture with too few words for its own word-count assertion — took less time to diagnose and fix than getting my toolchain into a state where I could actually run the project's real test suite.

**What did you learn about working in a large codebase?**
The biggest shift was learning to trust — and verify — assumptions about where a bug actually lives. My first instinct was to suspect the ReadmeScorer implementation itself, but tracing through _score_readme() line by line showed the word-counting logic was correct; the test fixture was the thing that was wrong. In a codebase with many interacting files (orchestrator.py, base.py, five different tool implementations), it mattered to isolate the actual unit under test rather than assume the bug was wherever the symptom showed up. I also learned that "passing tests" isn't the same as "correct tests" — a fixture can pass by accident (or fail by an off-by-one word count) without the underlying code being wrong at all.

**How did AI tools help — and where did they fall short?**
AI was most useful for quickly tracing through the regex logic in _score_readme() and confirming, word-count arithmetic and all, that the scorer's behavior was correct against each fixture — that kind of mechanical verification (running the actual class against test inputs, counting words, checking category boundaries) is exactly the kind of thing that's fast and reliable to hand off. It also helped catch the mypy type-annotation gaps across all 23 test methods in one pass rather than fixing them one error at a time.
Where it fell short: it couldn't run the project's actual make check / make test-unit in my real Windows environment, install pytest from the internet, or interact with Docker Desktop — all of that had to happen in my own terminal, and troubleshooting Git Bash path syntax, Scoop installs, and Docker startup was something I had to work through myself, screenshot by screenshot.

**What would you do differently if you started over?**
I'd set up and verify my full local environment (Git Bash, make, Docker Desktop, make setup) in Week 7 before touching any code, rather than discovering environment gaps midway through implementing the fix. I'd also scan the whole test file for similar boundary-condition mismatches earlier in the process, instead of treating it as a late cleanup step — it turned out there weren't any others in this file, but I didn't know that until I checked.

**What are you most proud of from this module?**
Diagnosing the root cause correctly on the first pass — recognizing that a failing test doesn't automatically mean the implementation is broken, and being able to prove it (running the fixture against the real ReadmeScorer class and confirming word_count = 51) instead of just guessing and rewriting the scorer to force the test to pass.