## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
When parsing resumes, the section header detection logic in `ResumeParser` (`ingestion/parsers/resume_parser.py`) uses regular expression patterns that strictly anchor headers to the start of a line without leading indentation. However, text extracted from PDFs or Markdown files commonly contains leading spaces or tabs before headers such as "Education:" or "Skills:". Because of this strict matching, indented headers fail to match and `detected_sections` returns empty. A successful fix will update the regex patterns in `_detect_sections()` to permit optional leading whitespace (`^[ \t]*`), enabling reliable section detection across all resume formats.

**Branch name:** fix/147-resume-fails-leading-whitespace

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[link to commit documenting the reproduced issue\]](https://github.com/ascherj/pathreview/commit/79fa96fd168ebfdcaf993f494a968d81d69f186e)

**Reproduction summary:**
I reproduced the issue by running the unit tests (specifically `test_detect_sections_with_leading_whitespace`). I observed that 6 unit tests failed because both the section header detection and markdown header stripping regexes strictly anchored matches to the absolute beginning of a line without permitting leading indentation (whitespace/tabs).

**PLAN.md link:** [\[link to PLAN.md in your fork\]](https://github.com/AlgoriThai07/pathreview/blob/fix/147-resume-fails-leading-whitespace/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have successfully implemented the fix for the section header detection issue in `ingestion/parsers/resume_parser.py`. I updated the regular expression patterns in the `_detect_sections` method to permit optional leading whitespace (spaces or tabs) before section headers. This was achieved by adding `^[ \t]*` to the beginning of the patterns that match section headers, which allows indented headers in resumes to be detected correctly.

**Next steps:**
The next steps are to verify that the fix works correctly by running the unit tests (specifically `test_detect_sections_with_leading_whitespace`), ensure code quality with `ruff check` and `black`, and finally submit a pull request with the changes.

**Blockers:**


---

### Check-in 2 (end of week)

**PR link:** [\[link to your submitted pull request\]](https://github.com/ascherj/pathreview/pull/540)

**Branch:** fix/147-resume-fails-leading-whitespace

**What you built:**
I have successfully updated the regular expression patterns in `ingestion/parsers/resume_parser.py` to permit optional leading whitespace before section headers in resumes. This was achieved by adding `^[ \t]*` to the beginning of the patterns that match section headers, which allows indented headers in resumes to be detected correctly.

**Tests added or updated:**
The tests added or updated are in `tests/unit/test_resume_parser.py`. 

**Self-review confirmation:** [X] make check passes [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
Reviewer feedback is not a feature in Summer 2026.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
I would say navigating through the codebase to find the actual file that is causing the bug is harder than I expected. I had to spend a lot of time just looking through files and trying to understand how the code works. I got to run `make test-unit` and `make test-integration` commands to help me identify the issue.

**What did you learn about working in a large codebase?**
I learned that working in a large codebase is not as intimidating as it seems. It's all about breaking down the problem into smaller pieces and taking it one step at a time. It's also important to remember that there are a lot of resources available to help you, such as the documentation and the community.

**What's different about contributing to someone else's production code**
I think the difference is that when I am building my own project. I could understand the code and how it works. However, with someone else's project, I had to spend a lot of time just looking through files and trying to understand how the code works and what the workflow is.

**How did AI tools help — and where did they fall short?**
I think AI tools help me a lot when it comes to understanding the codebase and how the code works. But it's not always accurate, so I had to double check everything. I think it falls short when it comes to understanding the big picture and the overall workflow of the project.

**What would you do differently if you started over?**
I would start by reading the documentation and understanding the codebase and the overall workflow of the project before jumping into the code. It's also important to remember that there are a lot of resources available to help you, such as the documentation and the community.

**What are you most proud of from this module?**
I am most proud of the fact that I was able to contribute to an open source project and that I was able to learn a lot about working in a large codebase. It's also rewarding to know that my code will help others use PathReview more effectively.