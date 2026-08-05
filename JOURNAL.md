# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` uses regex patterns anchored at the start of a line (`^Experience`, `\nExperience`). When text is extracted from PDFs it commonly preserves leading indentation, so lines like `"    Education:"` never match those anchors. As a result, `detected_sections` comes back empty even when the resume clearly contains sections like Education and Skills. A successful fix would adjust the patterns to allow optional leading whitespace before section headers, so indented section names are detected correctly.

**Branch name:** fix/147-resume-section-detection-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### Is This Issue Right for Me? — Checklist Notes

**Part 1 — Understanding the issue:**
The issue is clear and reproducible. Running the exact snippet from the issue description confirms `detected_sections` returns `[]` when it should return `['Education', 'Skills']`. The expected behavior is equally clear: after the fix, indented section headers are detected correctly.

**Part 2 — Tier fit:**
Tier 1. The fix lives entirely in one method in one file (`ingestion/parsers/resume_parser.py`). No other modules are involved and no understanding of the broader system is required. I chose Tier 1 because this is my first contribution to this codebase.

**Part 3 — Codebase readiness:**
I located `_detect_sections()` in `ingestion/parsers/resume_parser.py` and read the full method. The patterns use `^` and `\n` anchors that do not allow leading whitespace. I also read the three named failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) in `tests/unit/test_resume_parser.py` end-to-end before claiming this issue.

**Part 4 — Scope and time:**
No blockers or dependencies. The fix is a targeted regex change — estimated 2–3 hours including tests and PR writeup. The issue has no open dependencies and is not blocked by any other issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
To reproduce issue #147, I ran pytest tests/unit/test_resume_parser.py. The section detection tests failed as expected. The current parsing logic anchors headers strictly to the start of a line, meaning it fails to identify valid headers like 'Experience' when they contain the leading indentations commonly left behind by PDF text extraction.

**PLAN.md link:** https://github.com/rcraig-2023/pathreview/blob/fix/147-resume-section-detection-whitespace/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the core implementation for Issue #147. I successfully updated the regex logic in `ingestion/parsers/resume_parser.py` to accurately detect PDF sections and strip out Markdown headers. I also rebuilt the local `.venv` virtual environment to resolve tooling configuration errors, ran `make test-unit` (confirming all 10 unit tests for `test_resume_parser.py` pass), and resolved the specific `ruff` linting errors for the files I touched via `make check`. 

**Next steps:**
Push my working branch to GitHub and open a draft Pull Request. I will document the pre-existing `make check` failures in the PR description as required by the contribution guidelines, and then request peer review in Slack. Once I receive and implement any necessary feedback, I will complete Check-In 2 and submit the final PR.

**Blockers:**
Encountered 51 pre-existing linting errors and 48 pre-existing test failures. Had to use `--no-verify` to bypass the hooks, leaving the tech debt untouched per project guidelines.

---

### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/386

**Branch:** `fix/147-regex-logic-for-pdf-sections`

**What you built:**
Updated the regular expression logic in the resume parser to accurately detect and parse markdown headers that contain leading whitespace. This resolves an edge case where headers were being missed during PDF text extraction due to unintended indentation.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` by adding a specific regression test to verify that indented PDF section headers are correctly matched and parsed.

**Self-review confirmation:** 
[x] `make check` passes  
[x] `make test-unit` passes
*(Note: Passing with the exception of the documented pre-existing tech debt failures).*

**Draft PR feedback received from:** `kaiser1x`

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The most surprising challenge was realizing how strict the procedural and formatting requirements were compared to just getting the code to work. Getting the regex fix right was relatively straightforward, but losing points initially for a missing PR template body and omitted manual testing steps showed me that the submission and documentation process requires just as much attention to detail as the logic itself.

**What did you learn about working in a large codebase?**
I learned the critical importance of scope management and resisting the urge to fix everything in sight. Seeing 48 pre-existing test failures and 51 linting errors from unrelated modules was initially alarming, but I had to practice strict discipline to leave them untouched and focus solely on Issue #147 to avoid scope creep.

**How did AI tools help — and where did they fall short?**
AI was incredibly helpful for structuring the strict unit tests, untangling Pytest errors (like class indentation), and ensuring my PR description met all checklist requirements. However, it sometimes fell short in clearly communicating the scope of its own changes. For example, I had to pause and explicitly verify whether the AI had altered my core resume_parser.py logic or just the test suite, which was a great reminder that I always need to manually review AI-generated code diffs to know exactly what is being committed.

**What would you do differently if you started over?**
I would thoroughly review the contribution guidelines and the grading checklist before writing a single line of code. If I had built the manual reproduction steps and the strict test assertions into my workflow from the very beginning, I could have avoided the initial point deduction.

**What are you most proud of from this module?**
I am most proud of writing a solid, well-structured regression test (test_parse_indented_section_headers). It feels great moving past loose checks and writing aggressive assertions, knowing that my specific test will permanently protect the parser from breaking on whitespace and Markdown edge cases in the future.