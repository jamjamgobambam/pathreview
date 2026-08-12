# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**  
The resume parser uses the `_detect_sections()` function in `ingestion/parsers/resume_parser.py` to identify sections such as Education, Skills, and Experience. Right now, the function expects each section title to appear directly at the beginning of a line. When text extracted from a resume contains spaces before a section title, the parser does not recognize it and reports that the resume has no sections. The fix would allow the parser to ignore leading whitespace and correctly identify section titles in indented resume text.

**Branch name:** `fix/147-resume-section-leading-whitespace`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — “Is this issue right for me?”

I chose this issue because it is a Tier 1 problem with a clear scope and expected result. The issue appears to be limited to the resume section detection function and the regular expressions it uses to recognize section titles. It also includes examples of the failing input and identifies tests that can be used to confirm the solution. This makes the problem realistic for me to complete while still helping me practice reading an unfamiliar codebase, working with regular expressions, and testing a change.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/GildardoOrea/pathreview/commit/599df3e

**Reproduction summary:**  
I reproduced the issue by adding a unit test called `test_detect_sections_with_leading_whitespace` in `tests/unit/test_resume_parser.py` using the same indented resume text from the issue. The test fails because `_detect_sections()` returns an empty list, confirming that the regex patterns in `ingestion/parsers/resume_parser.py` do not recognize section titles when there is whitespace at the beginning of the line.

**PLAN.md link:** https://github.com/GildardoOrea/pathreview/blob/fix/147-resume-section-leading-whitespace/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**  
I am still deciding whether I should keep the existing patterns that use `\n` or simplify the list to only use the `^` patterns with `re.MULTILINE`, since they may become redundant. I plan to compare both approaches and make the final decision during Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**  
I made the main change in `_detect_sections()` inside `ingestion/parsers/resume_parser.py`. The parser now allows spaces or tabs before a section header, so sections like `Education:` and `Skills:` can still be detected when the resume text is indented. I also removed the two `\n` patterns after confirming that `re.MULTILINE` already allows `^` to match the beginning of every line. This answered the question I had left open in Week 8. I also updated the function docstring so the behavior is a little clearer.

**Next steps:**  
My next step is to add a couple more tests before finishing the fix. I want one test for tab-indented headers and another to make sure words like Experience or Skills are not detected when they are only part of a regular sentence. After that, I need to run `make check` and `make test-unit`, review the results against the baseline I recorded before making changes, open the PR against the upstream repository, and complete the PR template.

**Blockers:**  
The biggest blocker is that the repository already had a large number of failing tests and lint/type-checking issues before I started working on this issue. I saved the original results before making my changes, so I can compare them and make sure my fix does not introduce any new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/921

**Branch:** `fix/147-resume-section-leading-whitespace`

**What you built:**  
I fixed the resume section detection so headers like Education, Skills, and Experience can still be recognized when there are spaces or tabs before them. This is important because text copied or extracted from PDFs can keep extra indentation. The fix updates the regex so it accepts leading spaces or tabs and removes the older `\n` patterns because `re.MULTILINE` already handles the beginning of each line.

**Tests added or updated:**  
In `tests/unit/test_resume_parser.py`, I added `test_detect_sections_tab_indented` to check tab-indented headers and `test_detect_sections_ignores_header_word_mid_sentence` to make sure normal sentences are not treated as section titles. I also kept the Week 8 reproduction test, `test_detect_sections_with_leading_whitespace`. After the fix, the existing tests `test_detect_sections`, `test_parse_single_column_resume_text`, and `test_parse_resume_no_work_experience` also pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

The repository already had documented failures before I started. My baseline had 54 failing unit tests, along with existing ruff, mypy, and black issues. After my change, the unit test results were 50 failing and 381 passing. My fix corrected four previously failing tests and did not introduce new test, lint, type, or formatting problems in the files I changed.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**  
I have not received any reviewer or maintainer feedback on PR #921 yet. Since reviewer feedback is not required for this part of the course, I am leaving the PR open while I wait.

**How you responded:**  
There was no feedback to respond to, so I did not need to make any additional changes. I kept the PR open and made sure my branch stayed up to date.

---

### Reflection

**What was harder than you expected?**  
The actual code change was pretty small, but everything around it took more time than I expected. The hardest part was figuring out which test failures were related to my work and which ones were already in the repository. When I first ran the tests and saw 54 failures, I thought I had done something wrong. Recording the baseline before making changes helped me understand that the important question was whether my change introduced anything new, not whether the entire repository suddenly became perfect.

**What did you learn about working in a large codebase?**  
I learned that you spend a lot more time reading and understanding code than actually changing it. My fix only needed a small change, but I had to understand how `_detect_sections()` worked, how `^` behaves with `re.MULTILINE`, how the existing tests were written, and how the project expected commits and pull requests to be structured. On my own projects, I can usually choose whatever approach I want. In someone else's codebase, I also have to make sure my change fits the way the project is already organized and does not cause problems somewhere else. I also got more practice working with a fork, creating a branch, and opening a pull request against the upstream repository.

**How did AI tools help — and where did they fall short?**  
AI helped me the most when I was first trying to understand the codebase. It helped me find where the section detection was happening, understand what the regex was doing, and organize my plan and tests. At the same time, I could not just trust everything it generated. At one point, it created a test with the wrong indentation, which would have placed the test outside the class. I caught that while reviewing the code before committing it. There were also times when it made assumptions about the code that I had to check against the actual files. It helped me move faster, but I still had to read the code myself, check the diff, and run the tests to know whether the solution actually worked.

**What would you do differently if you started over?**  
I would set up the environment and run the baseline checks much earlier instead of waiting until I was closer to the deadline. I would also spend more time getting comfortable with the Git and pull request workflow at the beginning so I would not have to figure out those steps while trying to finish the assignment. I would also review generated code more carefully before committing it, especially tests, because small mistakes like incorrect indentation can create completely different problems.

**What are you most proud of from this module?**  
I am most proud that I was able to take a real issue in a codebase I had never worked with before, understand what was causing it, make a focused fix, add tests, and open a real pull request. I was also able to show that my change fixed four tests without adding new problems, even though the repository already had a lot of existing failures. I think keeping the fix focused on the issue instead of trying to fix everything else was one of the most important things I learned from this module.
